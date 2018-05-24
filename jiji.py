import os
import yaml
import string
import uuid
import logging

from collections import OrderedDict

logging.basicConfig(filename='jiji.log',level=logging.DEBUG)


class Dictionary:
    """A class for building language dictionaries in the JIJI format"""
    ABOUT_DICT_KEY = "_about_this_dictionary"

    def __init__(self, title, lang_from, lang_to=None, licence=''):
        self.title = title
        self.lang_from = lang_from
        self.lang_to = lang_to or lang_from
        self.licence = licence
        self.entries = []
        self.entries_by_lemma = {}

    def add_entry(self, entry):
        self.entries.append(entry)
        # Index the entry by lemma
        for l in entry.lemmas:
            if l not in self.entries_by_lemma:
                self.entries_by_lemma[l] = []
            self.entries_by_lemma[l].append(entry)

    def get_entries_by_lemma(self, lemma):
        if not lemma in self.entries_by_lemma:
            return []
        return self.entries_by_lemma[lemma]

    def validate(self):
        """Check validity of the dictionary and display a message for errors / inconsistencies"""
        pass

    def save(self, filename):
        """Write the jiji dictionary to a YAML file"""
        self.validate()
        with open(filename, 'w') as out:
            # Write about_this_dictionary information
            about = OrderedDict()
            about['title'] = self.title
            about['licence'] = self.licence
            about['languages'] = OrderedDict([('from', self.lang_from), ('to', self.lang_to)])
            out.write(yaml.dump({self.ABOUT_DICT_KEY: about}, default_flow_style=False, allow_unicode=True))

            # Write all entries
            entries = OrderedDict()
            for e in self.entries:
                try:
                    entries[e.get_entry_key()] = e.to_ordered_dict()
                except EntryWithoutSense:
                    logging.warning(f"Entry {e.id} has no sense defined, will skip.")
            out.write(yaml.dump(entries, default_flow_style=False, allow_unicode=True))


class EntryWithoutSense(Exception):
    pass


class Entry:
    def __init__(self, entry_id=None):
        self.id = entry_id or uuid.uuid4()
        self.lemmas = []
        self.senses = []
        self.tags = []
        self.pronunciations = []

    def add_lemma(self, lemma):
        lemma = lemma.strip()
        if lemma not in self.lemmas:
            self.lemmas.append(lemma)

    def add_sense(self, glosses, restriction= None):
        """Add a sense to this entry.
        A sense is composed of one or more glosses that are typically appended to form the sense definition
        If the sense concerns only some lemmas/pronounciations these can be passed in the restriction parameter"""
        sense = '/'.join(glosses).replace('\n', '')
        if restriction:
            if any(t not in self.lemmas and t not in self.pronunciations for t in restriction):
                raise RuntimeError(f"one of {restriction} is not in {self.lemmas} or {self.pronunciations}")
            sense = '(' + ', '.join(restriction) + ')' + sense
        self.senses.append(sense)

    def add_pronunciation(self, pronunciation):
        if ',' in pronunciation:
            raise RuntimeError(f"pronunciation must not contain a comma: {pronunciation}")
        if pronunciation not in self.pronunciations:
            self.pronunciations.append(pronunciation)

    def add_tag(self, tag):
        if ',' in tag:
            raise RuntimeError(f"tag must not contain a comma: {tag}")
        if tag not in self.tags:
            self.tags.append(tag)

    def get_entry_key(self):
        return ', '.join([l for l in self.lemmas])

    def to_ordered_dict(self):
        entry = OrderedDict()
        if not self.senses:
            raise EntryWithoutSense()
        if len(self.senses) > 1:
            entry['senses'] = self.senses
        else:
            entry['sense'] = self.senses[0]
        if self.pronunciations:
            entry['pronunciation'] = ', '.join(self.pronunciations)
        if self.tags:
            entry['tags'] = ', '.join(self.tags)
        return entry


def tag_dictionary(dict, tag_filepath, tag_multiple_entries=True, pick_lowest_tag=True, add_line_number=False):
    """Add tags to a dictionary entries based on a text file containing lemmas.
    The text file must contain one lemma per line, the corresponding entries in the
    dictionary will be tagged with the name of the text file.
    """
    basename = os.path.basename(tag_filepath)
    filename = os.path.splitext(basename)[0]
    line_number = 0
    with open(tag_filepath) as f:
        lines = f.readlines()
        for l in lines:
            line_number += 1
            lemma = l.strip()
            entries = dict.get_entries_by_lemma(lemma)
            if not entries:
                logging.warning(f"Cannot tag lemma {lemma} because it was not found in the dictionary.")
            elif not tag_multiple_entries and len(entries) > 1:
                entries_ids = ', '.join([e.id for e in entries])
                logging.warning(f"Cannot tag lemma {lemma} because there are more than one entry in the dictionary {entries_ids}.")
            else:
                lemma_tag = (filename + str(line_number)) if add_line_number else filename
                for e in entries:
                    tag_entry(e, lemma_tag, pick_lowest_tag)


def tag_entry(entry, tag, pick_lowest_tag):
    """Add a tag to a dictionary entry
    In case of numbered tag like freq1 / freq2 / ..., only one number is allowed
    and for now we pick the lowest by convention.
    """
    if tag in entry.tags:
        return
    same_numbered_tag = [t for t in entry.tags if t.rstrip(string.digits) == tag.rstrip(string.digits)]
    if not same_numbered_tag:
        entry.add_tag(tag)
        return
    # There is already a numbered tag identical to this one, pick the lowest number
    if len(same_numbered_tag) > 1:
        raise RuntimeError(f"entry {entry.id} has multiple occurrences of numbered tag")
    same_numbered_tag = same_numbered_tag[0]
    idx = len(tag.rstrip(string.digits))
    factor = 1 if pick_lowest_tag else -1
    if int(tag[idx:]) * factor < int(same_numbered_tag[idx:]) * factor:
        entry.tags.remove(same_numbered_tag)
        entry.add_tag(tag)


# Somehow yaml needs some strange initialization to work with OrderedDict
# See https://stackoverflow.com/a/31609484/257272
def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(OrderedDict, represent_dict_order)
setup_yaml()