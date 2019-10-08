import os
import string
from unicodedata import normalize

class PathSanitiser(object):
    EMPTY_NAME = "empty"

    empty_index = 0
    root_path = ""

    def __init__(self, root_path):
        self.root_path = root_path

    # check if directory for output is exists,
    # make directory if it does not
    def ensure_directory_exists(self, path_directory):
        if not os.path.exists(path_directory):
            os.mkdir(path_directory)

    # return path with separators for specific OS
    def os_path_separators(self):
        seps = []
        for sep in os.path.sep, os.path.altsep:
            if sep:
                seps.append(sep)

        return seps

    # return a valid filename
    def sanitise_filesystem_name(self, potential_file_path_name):
        # sort out unicode characters
        valid_filename = normalize("NFKD", potential_file_path_name).encode(
            "ascii", "ignore").decode("ascii")

        # replace path separators with underscores
        for sep in self.os_path_separators():
            valid_filename = valid_filename.replace(sep, "_")

        # ensure only valid characters
        valid_chars = "-_.() {0}{1}".format(string.ascii_letters,
                                            string.digits)
        valid_filename = "".join(
            ch for ch in valid_filename if ch in valid_chars)

        # ensure at least one letter of number to ignore names such as ".."
        valid_chars = "{0}{1}".format(string.ascii_letters, string.digits)
        test_filename = "".join(
            ch for ch in potential_file_path_name if ch in valid_chars)
        if len(test_filename) == 0:
            # replace empty file name or file path part with the following
            valid_filename = self.EMPTY_NAME + "_" + str(self.empty_index)
            self.empty_index += 1

        return valid_filename

    # add root path
    def get_root_path(self):
        # replace with your own root file path
        filepath = self.root_path
        filepath = os.path.abspath(filepath)

        # ensure trailing path separator
        if not any(filepath[-1] == sep for sep in self.os_path_separators()):
            filepath = "{0}{1}".format(filepath, os.path.sep)
        self.ensure_directory_exists(filepath)
        return filepath

    def path_split_into_list(self, path):
      # get all parts of the path as a list, excluding path separators
      parts = []
      while True:
        newpath, tail = os.path.split(path)
        if newpath == path:
          assert not tail
          if path and path not in self.os_path_separators():
            parts.append(path)
          break

        if tail and tail not in self.os_path_separators():
          parts.append(tail)

        path = newpath

      parts.reverse()
      return parts

    def sanitise_filesystem_path(self, potential_file_path):
        # Splits up a path and sanitises the name of each part separately
        path_parts_list = self.path_split_into_list(potential_file_path)
        sanitised_path = ''
        for path_component in path_parts_list:
            sanitised_path = '{0}{1}{2}'.format(sanitised_path,
                self.sanitise_filesystem_name(path_component),
                os.path.sep)
        return sanitised_path

    def check_if_path_is_under(self, parent_path, child_path):
        # Using the function to split paths into lists of component parts, check that one path is underneath another
        child_parts = self.path_split_into_list(child_path)
        parent_parts = self.path_split_into_list(parent_path)
        if len(parent_parts) > len(child_parts):
            return False
        return all(part1==part2 for part1, part2 in zip(child_parts, parent_parts))

    def make_valid_file_path(self, path=None, filename=None):
        root_path = self.get_root_path()
        if path:
            sanitised_path = self.sanitise_filesystem_path(path)
            if filename:
                sanitised_filename = self.sanitise_filesystem_name(filename)
                complete_path = os.path.join(root_path, sanitised_path, sanitised_filename)
            else:
                complete_path = os.path.join(root_path, sanitised_path)
        else:
            if filename:
                sanitised_filename = self.sanitise_filesystem_name(filename)
                complete_path = os.path.join(root_path, sanitised_filename)
            else:
                complete_path = complete_path
        complete_path = os.path.abspath(complete_path)
        if self.check_if_path_is_under(root_path, complete_path):
            return complete_path
        else:
            return None
