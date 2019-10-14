"""
  Reads Webpack source maps and extracts the disclosed un-compiled/commented source code for review.
  Can detect and attempt to read sourcemaps from Webpack bundles with the `-d` flag.
  Put source into a directory structure similar to dev.
"""

import argparse
import sys
from src.source_map_extractor import SourceMapExtractor

def main():
    parser = argparse.ArgumentParser(
        description="A tool to extract code from Webpack sourcemaps. Turns black boxes into gray ones.")
    parser.add_argument("-l", "--local", action="store_true", default=False)
    parser.add_argument("-d", "--detect", action="store_true", default=False,
                        help="Attempt to detect sourcemaps from JS assets in retrieved HTML.")
    parser.add_argument("--make-directory", action="store_true", default=False,
                        help="Make the output directory if it doesn't exist.")
    parser.add_argument("--dangerously-write-paths", action="store_true", default="False",
                        help="Write full paths. WARNING: Be careful here, you are pulling directories from an untrusted source.")

    parser.add_argument("uri_or_file", help="The target URI or file.")
    parser.add_argument("output_directory",
                        help="Directory to output from sourcemap to.")

    if (len(sys.argv) < 3):
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    extractor = SourceMapExtractor(vars(args))
    extractor.run()


if __name__ == "__main__":
    main()
