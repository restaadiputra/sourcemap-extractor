import argparse
import json
import os
import re
import string
import sys
import requests
from urllib.parse import urlparse
from unicodedata import normalize
from bs4 import BeautifulSoup, SoupStrainer

from src.path_sanitiser import PathSanitiser
from src.source_map_extractor_error import SourceMapExtractorError

class SourceMapExtractor(object):
    """Primary SourceMapExtractor class. Feed this arguments."""

    _target = None
    _is_local = False
    _attempt_sourcemap_detection = False
    _output_directory = ""
    _target_extracted_sourcemaps = []

    _path_sanitiser = None


    def __init__(self, options):

        if 'output_directory' not in options:
            raise SourceMapExtractorError("output_directory must be set in options.")
        else:
            self._output_directory = os.path.abspath(options['output_directory'])
            if not os.path.isdir(self._output_directory):
                os.mkdir(self._output_directory)
                
        self._path_sanitiser = PathSanitiser(self._output_directory)

        if options['local'] == True:
            self._is_local = True

        if options['detect'] == True:
            self._attempt_sourcemap_detection = True

        self._validate_target(options['uri_or_file'])

    def run(self):
        """Run extraction process."""
        if self._is_local == False:
            if self._attempt_sourcemap_detection:
                detected_sourcemaps = self._detect_js_sourcemaps(self._target)
                for sourcemap in detected_sourcemaps:
                    self._parse_remote_sourcemap(sourcemap)
            else:
                self._parse_remote_sourcemap(self._target)

        else:
            self._parse_sourcemap(self._target)

    def _validate_target(self, target):
        """Basic validation on the target."""
        parsed = urlparse(target)
        if self._is_local is True:
            self._target = os.path.abspath(target)
            if not os.path.isfile(self._target):
                raise SourceMapExtractorError("uri_or_file is set to be a file, but doesn't seem to exist. check your path.")
        else:
            if parsed.scheme == "":
                raise SourceMapExtractorError("uri_or_file isn't a URI, and --local was not set. set --local?")
            file, ext = os.path.splitext(parsed.path)
            self._target = target
            if ext != '.map' and self._attempt_sourcemap_detection is False:
                print("WARNING: URI does not have .map extension, and --detect is not flagged.")

    def _detect_js_sourcemaps(self, uri):
        """Pull HTML and attempt to find JS files, then read the JS files and look for sourceMappingURL."""
        remote_sourcemaps = []
        data = self._get_remote_data(uri)

        print("Detecting sourcemaps in HTML at %s" % uri)
        script_strainer = SoupStrainer("script", src=True)
        try:
            soup = BeautifulSoup(data, "html.parser", parse_only=script_strainer)
        except:
            raise SourceMapExtractorError("Could not parse HTML at URI %s" % uri)

        for script in soup:
            source = script['src']
            parsed_uri = urlparse(source)
            
            next_target_uri = ""
            if parsed_uri.scheme != '':
                next_target_uri = source
            else:
                current_uri = urlparse(uri)
                built_uri = current_uri.scheme + "://" + current_uri.netloc + source
                next_target_uri = built_uri
 
            js_data = self._get_remote_data(next_target_uri)
            
            # get last line of file
            last_line = js_data.split("\n")[-1].strip()
            regex = "\\/\\/#\s*sourceMappingURL=(.*)$"
            matches = re.search(regex, last_line)

            if matches:
                asset = matches.groups(0)[0].strip()
                asset_target = urlparse(asset)
                
                if asset_target.scheme != '':
                    print("Detected sourcemap at remote location %s" % asset)
                    remote_sourcemaps.append(asset)
                else:
                    current_uri = urlparse(next_target_uri)
                    asset_uri = current_uri.scheme + '://' + \
                        current_uri.netloc + \
                        os.path.dirname(current_uri.path) + \
                        '/' + asset
                    
                    print("Detected sourcemap at remote location %s" % asset_uri)
                    remote_sourcemaps.append(asset_uri)
        
        return remote_sourcemaps

    def _parse_sourcemap(self, target, is_str=False):
        map_data = ""
        if is_str is False:
            if os.path.isfile(target):
                with open(target, 'r') as f:
                    map_data = f.read()
        else:
            map_data = target

        # with the sourcemap data, pull directory structures
        try:
            map_object = json.loads(map_data)
        except json.JSONDecodeError:
            print("ERROR: Failed to parse sourcemap %s. Are you sure this is a sourcemap?" % target)
            return False

        # we need `sourcesContent` and `sources`.
        # do a basic validation check to make sure these exist and agree.
        if 'sources' not in map_object or 'sourcesContent' not in map_object:
            print("ERROR: Sourcemap does not contain sources and/or sourcesContent, cannot extract.")
            return False

        if len(map_object['sources']) != len(map_object['sourcesContent']):
            print("WARNING: sources != sourcesContent, filenames may not match content")

        idx = 0
        for source in map_object['sources']:
            if idx < len(map_object['sourcesContent']):
                path = source
                content = map_object['sourcesContent'][idx]
                idx += 1

                # remove webpack:// from paths
                # and do some checks on it
                write_path = self._get_sanitised_file_path(source)
                if write_path is not None:
                    os.makedirs(os.path.dirname(write_path), mode=0o755, exist_ok=True)
                    with open(write_path, 'w') as f:
                        print("Writing %s..." % os.path.relpath(write_path))
                        f.write(content)
            else:
                break
    
    def _parse_remote_sourcemap(self, uri):
        """GET a remote sourcemap and parse it."""
        data = self._get_remote_data(uri)
        if data is not None:
            self._parse_sourcemap(data, True)
        else:
            print("WARNING: Could not retrieve sourcemap from URI %s" % uri)

    def _get_sanitised_file_path(self, sourcePath):
        """Sanitise webpack paths for separators/relative paths"""
        sourcePath = sourcePath.replace("webpack:///", "")
        exts = sourcePath.split(" ")

        if exts[0] == "external":
            print("WARNING: Found external sourcemap %s, not currently supported. Skipping" % exts[1])
            return None

        path, filename = os.path.split(sourcePath)
        if path[:2] == './':
            path = path[2:]
        if path[:3] == '../':
            path = 'parent_dir/' + path[3:]
        if path[:1] == '.':
            path = ""

        filepath = self._path_sanitiser.make_valid_file_path(path, filename)
        return filepath

    def _get_remote_data(self, uri):
        """Get remote data via http."""
        result = requests.get(uri)

        if result.status_code == 200:
            return result.text
        else:
            print("WARNING: Got status code %d for URI %s" % (uri, result.status_code))
            return False
