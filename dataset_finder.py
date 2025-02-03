import os
import yaml

from tabulate import tabulate


def extract_from_format(format_string, input_string):
    """
    Extract values from an input string according to a given format string.
    Values to be extracted should be surrounded by {} in the format string.
    Raises an error if the input string does not otherwise match the format string.
    If a variable name is "*", the matched value will be ignored instead of returned.
    This function uses the characters proceeding the end brace } to determine where
    the match ends in the input string. Therefore, if those characters themselves
    are the value intended to be matched, the strings will be considered mismatched.
    Example: If attempting to match "{a}_{b}" with a string where the value of "a" is
    intended to be "1_2", only the "1" would be matched to "a". This is usually only
    a problem if the separator between variables is a single character.
    Inputs:
    - format_string - a string containing the format, with {} around variables
    - input_string - a string following the format whose values are to be extracted
    Returns:
    A dictionary mapping the names of the variables from format_string to the values found in input_string.
    """
    extracted_values = {}
    while format_string:
        
        # no variables left
        if "{" not in format_string:
            break
        
        # find argument start point
        arg_start = format_string.find("{")
    
        # cut out non-variable filler (for example, "v1-r1-ACS-{bc}-{ref}" will become "bc}-{ref}"
        # but first check it matches just in case the strings aren't the same format
        if format_string[:arg_start] != input_string[:arg_start]:
            raise ValueError("Strings are not the same format, values cannot be matched")
            # break
        
        format_string = format_string[arg_start + 1:]
        input_string = input_string[arg_start:]
    
        # find the next character after variable and use it to extract from check string
        arg_end = format_string.find("}")
        var_name = format_string[:arg_end]
        # sep = format_string[arg_end + 1]
        format_string = format_string[arg_end + 1:]

        # check if at end (i.e. nothing more to cut out)
        if format_string:
            # get the separator (multiple characters to allow for year filtering later)
            if "{" in format_string:
                sep_end = format_string.find("{")
                sep = format_string[:sep_end]
            else:
                sep = format_string
            sep_pos = input_string.find(sep)
            var_value = input_string[:sep_pos]
            input_string = input_string[sep_pos:]
        else:
            var_value = input_string

        # match all - don't raise an error, but also don't keep result
        if var_name != "*":
            extracted_values[var_name] = var_value
    
    return extracted_values


# important: this can be done in-place
def match_values(arr, format_string, search_terms, exact_match = False, in_place = True, exact_match_dict = {}):
    """
    Takes a list of strings, extracts their values according to the given format, and tries to match them against
    a given dictionary of search terms. Results that do not match are removed from the list (in place by default).
    Each given search term can be assigned multiple values - only one of them needs to match for the string to be kept.
    There is the option to match exactly or not (in which case any given search term is considered a match if it
    is a substring of the string it is being tested against). Additionally, individual terms can be designated
    to be exact match terms or not, overriding the global value.
    Matches are not case sensitive, even if exact_match is True.
    Inputs:
    - arr: A list of strings in the format given by format_string
    - format_string: The format which will be used to extract values out of array strings for matching
    - search_terms: A dictionary mapping variables names to values (can be individual or list for each value)
    - exact_match: Whether to match exactly or by substring (default False)
    - in_place: Whether to modify arr in place or to create and return a new array (default True)
    - exact_match_dict: A dictionary mapping variable names to True or False values for whether they should
    be exact matches. If a given variable name is not included, exact_match will be used instead
    Output:
    The original array of strings with any non-matching strings removed, or a new array with all matching
    strings included, depending on in_place.
    """
    # turn strings into lists with a single term so that later loops don't loop by letter
    for key in search_terms:
        if isinstance(search_terms[key], str):
            search_terms[key] = [search_terms[key]]

    to_remove = []

    for item in arr:

        try:
            extracted_values = extract_from_format(format_string, item)
    
            for key in extracted_values:
                
                # check if it's being searched by - if not, match by default
                if key in search_terms:
                    remove = True
                    check_value = extracted_values[key]
                    for value in search_terms[key]:
                        if exact_match_dict[key] if key in exact_match_dict else exact_match:
                            if value.casefold() == check_value.casefold():
                                remove = False
                        else:
                            if value.casefold() in check_value.casefold():
                                remove = False
                    if remove:
                        to_remove.append(item)
                        
                # already failed against one of the search terms, can move on to next item
                if item in to_remove:
                    break

        # failed to match properly
        except:
            to_remove.append(item)

    # use string method to modify existing list
    if in_place:
        for item in to_remove:
            arr.remove(item)
        return arr

    # create new list
    else:
        new_arr = [item for item in arr if item not in to_remove]
        return new_arr


class dataset_info:
    def __init__(self, data, root, format_file):
        self.data = data
        self.root = root
        self.format_file = format_file
        self.info = ""
        self.selected = {}
        self.exact_match_dict = {}

    def __repr__(self):
        return tabulate([*self.data.items()])

    def _repr_html_(self):
        return tabulate([*self.data.items()], tablefmt = "html", headers=["Key", "Value"])

    def select(self, exact_match = False, **kwargs):
        for key in kwargs:
            self.selected[key] = kwargs[key]
            self.exact_match_dict[key] = exact_match
        return self

    def deselect(self, *args):
        for key in args:
            if key in self.selected:
                self.selected.pop(key)
                self.exact_match_dict.pop(key)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def generate_info(self, apply_filter = False, exact_match = False):

        if self.format_file[0] == os.sep:
            format_file = self.format_file[1:]
        else:
            format_file = self.format_file
        
        if "{" in format_file:
            
            first_arg_pos = format_file.find("{")
    
            # cut off by folder in case the variable wasn't immediately after /
            slash_pos = format_file[first_arg_pos::-1].find(os.sep)
            if slash_pos == -1:
                prev_separator_pos = -1
            else:
                prev_separator_pos = first_arg_pos - slash_pos
    
            start_path = self.root + format_file[:prev_separator_pos + 1]
            format_file = format_file[prev_separator_pos + 1:]

        else:
            start_path = self.root + format_file
            format_file = ""

        for root, dirs, files in os.walk(start_path):
            dirs.sort()
            files.sort()

            # how deep we are into the tree (root = 0)
            level = 0

            short_root = root.replace(start_path, '')
            if root != start_path:
                level = short_root.count(os.sep) + 1

            if level == format_file.count(os.sep):
                for i, file in enumerate(files):
                    files[i] = short_root + os.sep + file

                if apply_filter and self.selected:
                    match_values(files, format_file, self.selected, in_place = True, exact_match_dict = self.exact_match_dict)                
                
                for file in files:
                    values = {key: value for key, value in extract_from_format(format_file, file).items() if key not in self.data}
                    yield values, file
    
    def collate_info(self):
        def collate_info_recursive(current_dict, info):
            key = list(info.keys())[0]
            value = info.pop(key)
        
            if key in current_dict:
                if not info:
                    current_dict[key][value] = {}
                else:
                    if value not in current_dict[key]:
                        new_dict = {}
                        current_dict[key][value] = new_dict
                    collate_info_recursive(current_dict[key][value], info)
        
            if key not in current_dict:
                if not info:
                    current_dict[key] = {value: {}}
                else:
                    new_dict = {}
                    current_dict[key] = {value: new_dict}
                    collate_info_recursive(new_dict, info)

        collated_info = {}
        for info, file in self.generate_info():
            collate_info_recursive(collated_info, info)
        return collated_info

    def print_info(self):
        if self.info:
            return self.info
            
        def print_info_recursive(current_info, depth = 0):
            if not current_info:
                return ""
            var_name, info = list(current_info.items())[0]
            keys = list(info.keys())
            out_str = ""
            while keys:
                key = keys[0]
                merged_keys = [key]
                value = info[key]
                for next_key in keys[1:]:
                    if info[next_key] == value:
                        merged_keys.append(next_key)

                out_str = out_str + "   " * depth + f"{var_name}: {merge_values(merged_keys)}"
                if value:
                    out_str = out_str + "\n" + print_info_recursive(value, depth + 1)

                for item in merged_keys:
                    keys.remove(item)

                if keys:
                    out_str = out_str + "\n\n"

            return out_str
        
        collated_info = self.collate_info()
        self.info = print_info_recursive(collated_info)
        print(self.info)
        # return self.info
    
    def match(self, key, match_terms, exact_match = False):
        if isinstance(match_terms, str):
            match_terms = [match_terms]
        if exact_match:
            return any(term == self.data[key] for term in match_terms)
        else:
            return any(term in self.data[key] for term in match_terms)

    def __iter__(self):
        return iter(self.get_files())

    def get_files(self):
        return [(self.root + file).replace(2 * os.sep, os.sep) for (info, file) in self.generate_info(True)]


class dataset_info_collection:
    def __init__(self, items = []):
        self.items = []

    def add(self, item):
        self.items.append(item)

    # select variables within the dataset to include
    def select(self, exact_match = False, **kwargs):
        for item in self.items:
            item.select(exact_match, **kwargs)

    # deselect variables
    def deselect(self, *args):
        for item in self.items:
            item.deselect(*args)

    # return all the files from all the dataset_info objects in a single 1D list
    def get_files(self):
        files = []
        for item in self.items:
            files = files + item.get_files()
        return files

    # so that open_mfdataset can be used directly with this object
    def __iter__(self):
        return iter(self.get_files())

    # allows individual dataset_info objects to be extracted directly
    # needs improvement, a slice should return a new dataset_info_collection
    # containing all the objects instead of a list (to preserve class methods)
    def __getitem__(self, key):
        return self.items[key]

    def __repr__(self):
        return tabulate([item.data for item in self.items], headers = "keys", showindex = True)

    # display nicely when interrogating on JupyterLab
    def _repr_html_(self):
        return tabulate([item.data for item in self.items], headers = "keys", showindex = True, tablefmt = "html")


def filter_all(format_dirs, format_file, exact_match = False, **kwargs):
    """
    Search through a directory and its subdirectories, filtering out results that do not match
    according to the given format strings and supplied variables, returning a list of applicable datasets.
    Here "dataset" is defined slightly arbitrarily and may need clarification.
    Essentially, format_dirs + format_file should compose the entire path of any single data file,
    but format_dirs is where the filter function will stop, with any subdirectories in format_file
    considered to be a part of the dataset. This could include different weather variables so that
    they are grouped together instead of being listed as separate datasets.
    For example:
    If a file's format is /a/b/c/{x}/{y}/{z}/{var}/{year}.nc, format_dirs could be "/a/b/c/{x}/{y}/{z}/"
    and format_file could be /{var}/{year}.nc. An individual returned result would be an "{x} {y} {z}"
    dataset, with any variables it contains being considered a part of it.
    For simplicity this could simply encapsulate every subdirectory. If this is the case it is still
    important to keep the file format itself separate as only directories are checked in this function.
    Input:
    format_dirs: The format of the directories leading to the datasets
    format_file: The format of the files within the datasets, which can include subdirectories
    exact_match: Whether to match search terms exactly, default to False. Otherwise a substring 
    is considered a match
    **kwargs: Keyword arguments mapping search terms to values for matching. Multiple values can
    be assigned to each search term - only one needs to match for it to be included.
    Output:
    A dataset_info_collection object containing a list of dataset_info objects corresponding to
    successful matches.
    """

    # internal helper function, can't be used from outside
    # walk through directory tree to find datasets, filtering by matching names against columns along the way
    def filter_walk(start_path, columns, exact_match = False, **kwargs):
        for root, dirs, files in os.walk(start_path):
            dirs.sort()
    
            # how deep we are into the tree (root = 0)
            level = 0
            
            if root != start_path:
                level = root.replace(start_path, '').count(os.sep) + 1
    
            # stopping point - no more columns to check against
            if level >= len(columns):
                # yield turns this function into a generator instead of manually constructing
                # and returning a list then looping through it later
                # the code will resume from here when the next entry is required
                yield root.replace(start_path, ''), dirs
    
                # stops the os.walk from travelling any deeper
                dirs.clear()
    
            # match directory names against given filters to stop os.walk from finding unwanted datasets
            else:
    
                # if key wasn't provided, nothing will be filtered out
                match_values(dirs, columns[level], kwargs, exact_match, in_place = True)

    # find root of string by looking for first variable
    if "{" in format_dirs:
        first_arg_pos = format_dirs.find("{")

        # cut off by folder in case the variable wasn't immediately after /
        slash_pos = format_dirs[first_arg_pos::-1].find(os.sep)
        if slash_pos == -1:
            prev_separator_pos = -1
        else:
            prev_separator_pos = first_arg_pos - slash_pos

        start_path = format_dirs[:prev_separator_pos + 1]
        columns = format_dirs[prev_separator_pos + 1:].split(os.sep)

        # remove empty final column which shows up from the split if path string ended in /
        if not columns[-1]:
            columns.pop()

    else:
        start_path = format_dirs
        columns = []
    
    all_data = dataset_info_collection()
        
    for root, dirs in filter_walk(start_path, columns, exact_match, **kwargs):
        info = extract_from_format(os.sep.join(columns), root)
        dataset = dataset_info(info, format_dirs.format(**info), format_file)
        all_data.add(dataset)

    return all_data

    
def merge_values(values):
    """
    Merge a list of strings into a single nice string.
    This is mostly for the purpose of cleaning up a big list of years for readability.
    If not all inputs can be converted into integers, it will simply return a comma separated list.
    Otherwise, it will attempt to group integers (in the format "start to end") if they are consecutive. 
    If there are multiple non-continuous groups of integers, they will be comma separated.
    Example: If values = ["1960", "1961", "1962", "1963", "1964", "1970", "1971", "1972"],
    then the output will be "1960 to 1964, 1970 to 1972".
    Inputs:
    - values: the list of strings to merge
    Output:
    A single string joining the values as specified.
    """
    if all([item.isdigit() for item in values]):
        numbers = sorted([int(value) for value in values])
        start_number = numbers.pop(0)
        out_str = f"{start_number}"
        end_number = start_number
        previous_number = start_number
        while numbers:
            next_number = numbers.pop(0)
            if next_number == previous_number + 1:
                end_number = next_number
            else:
                if start_number != end_number:
                    out_str = out_str + f" to {end_number}"
                start_number = next_number
                end_number = start_number
                out_str = out_str + f", {start_number}"

            previous_number = next_number
                
        if start_number != end_number:
            out_str = out_str + f" to {end_number}"

        return out_str
        
    return ", ".join(values)


def year_range(start: int = None, end: int = None, step: int = 1, inclusive: bool = True):
    """
    Generates a list of year strings from between "start" and "end" for the purposes of string matching.
    In general, matches the output of range(start, end, step), but will behave slightly differently
    if only one input is given (it will be treated as the start instead of the end.
    Also, defaults to including the end point which range() does not.
    Inputs:
    - start: int representing start year. If not specified or None, defaults to 1800
    - end: int representing end year. If not specified or None, defaults to 2200
    - step: int representing step count. Defaults to 1 (i.e. include every year)
    - inclusive: bool for whether or not to include the end point. Defaults to True for ease of use
    Outputs:
    A list of strings according to the given parameters.
    """
    
    # default values, though there's probably a better solution here (with slices or maybe regexps up the line)
    if start is None:
        start = 1800
    if end is None:
        end = 2200
        
    return [str(year) for year in range(start, end + 1 if inclusive else 0, step)]


def paths(key, yaml_path = "paths.yml"):
    """
    Use a yaml file to record paths in advance and load them by key.
    Return a function that calls filter_all with the appropriate paths.
    Inputs:
    - key: The name of the paths being referenced within the yaml file
    - yaml_path: The path of the yaml file (default "paths.yml" in working directory)
    Returns:
    A function calling filter_all with the file path arguments already assigned    
    """
    with open(yaml_path, 'r') as fstream:
        keys = yaml.safe_load(fstream)

    format_dirs = keys[key]["format_dirs"]
    format_file = keys[key]["format_file"]

    def use_paths(exact_match = False, **kwargs):
        return filter_all(format_dirs, format_file, exact_match, **kwargs)

    return use_paths


def get_datasets(key, yaml_path = "paths.yml", exact_match = False, **kwargs):
    """
    Use a yaml file to get path formats, then immediately search and return dataset matches.
    Identical to "paths" above except removes an intermediate step.
    """
    return paths(key, yaml_path)(exact_match, **kwargs)

