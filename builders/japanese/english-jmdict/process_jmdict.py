import xml.etree.ElementTree as etree

import jiji
from tools import download

"""
This script process the JMDict XML file and output jiji dictionary
JMdict project page => http://www.edrdg.org/jmdict/j_jmdict.html
JMDict DTD => http://www.edrdg.org/jmdict/jmdict_dtd_h.html
JMdict_e is the jmdict dictionary with only the english translations
----------------------------------------------------------------
Here is a sample entry for JMdict XML format

<entry>
    <ent_seq>1000110</ent_seq>
    <k_ele>
        <keb>ＣＤプレーヤー</keb>
        <ke_pri>spec1</ke_pri>
    </k_ele>
    <k_ele>
        <keb>ＣＤプレイヤー</keb>
    </k_ele>
    <r_ele>
        <reb>シーディープレーヤー</reb>
        <re_restr>ＣＤプレーヤー</re_restr>
        <re_pri>spec1</re_pri>
    </r_ele>
    <r_ele>
        <reb>シーディープレイヤー</reb>
        <re_restr>ＣＤプレイヤー</re_restr>
    </r_ele>
    <sense>
        <pos>&n;</pos>
        <gloss>CD player</gloss>
    </sense>
    <sense>
        <gloss>audio player</gloss>
        <gloss>audio CD player</gloss>
    </sense>
</entry>

In particular we want to keep the word kanji forms(<keb> tag), kana forms(<reb> tag), and meaning(<sense> tag)
"""


TAGS_FILES_OPTS = (
    'stopword.txt',
    ('jlpt1.txt', {'pick_lowest_tag': False}),
    ('jlpt2.txt', {'pick_lowest_tag': False}),
    ('jlpt3.txt', {'pick_lowest_tag': False}),
    ('jlpt4.txt', {'pick_lowest_tag': False}),
    ('jlpt5.txt', {'pick_lowest_tag': False}),
    'freq01.txt',
    'freq02.txt',
    'freq03.txt',
    'freq04.txt',
    'freq05.txt',
    'freq06.txt',
    'freq07.txt',
    'freq08.txt',
    'freq09.txt',
    'freq10.txt',
    'freq11.txt',
    'freq12.txt'
)
WRITTEN_WITH_KANA_PROP = 'word usually written using kana alone'


jmdict = download.download_if_modified('ftp://ftp.monash.edu.au/pub/nihongo/JMdict_e.gz')
#jmdict = '/home/julian/Prog/github.com/jiji/builders/japanese/english-jmdict/work/JMdict_e'

jiji_dict = jiji.Dictionary(
    title="Jim's Breen Japanese dictionary",
    lang_from='Japanese',
    lang_to='English',
    licence='Creative Commons Attribution-ShareAlike Licence (V3.0)'
)


def read_dictionary():
    with open(jmdict, 'r') as xml_file:
        tree = etree.parse(xml_file)
        root = tree.getroot()
        for entry in root:
            process_jmdict_entry(entry)


def process_jmdict_entry(xml_entry):
    """Process one entry of the english-jmdict xml file"""
    entry_number = xml_entry.find('ent_seq').text
    entry = jiji.Entry(entry_number)
    lemmas = []

    # Add kanji forms as lemma
    has_kanji = bool(xml_entry.findall('./k_ele/keb'))
    if has_kanji:
        for keb in xml_entry.findall('./k_ele/keb'):
            kjf = keb.text.strip()
            lemmas.append(kjf)

    # Add kana form as pronunciation or lemma
    readings = [JmdictReading(xml_node) for xml_node in xml_entry.findall('r_ele')]
    if not has_kanji:
        for r in readings:
            lemmas.append(r.text)

    # Create entry and add senses for all lemma or only particular lemma
    senses = [JmdictSense(xml_node) for xml_node in xml_entry.findall('sense') if xml_node.findall('gloss')]
    for s in senses:
        if s.is_usually_kana:
            # if the sense is usually written in kana, we must add the sense readings to the list of possible lemmas
            for sense_reading in s.get_readings(readings):
                if sense_reading.text not in lemmas:
                    lemmas.append(sense_reading.text)
                if s.has_restriction():
                    s.readings_restriction.add(sense_reading.text)

    for l in lemmas:
        entry.add_lemma(l)

    for r in readings:
        if r.text not in lemmas:
            entry.add_pronunciation(r.text)

    for s in senses:
        entry.add_sense(s.glosses, s.lemmas_restriction | s.readings_restriction)

    # Add nfxx tags concerning word frequency
    tags = {n.text for n in xml_entry.findall('./k_ele/ke_pri') + xml_entry.findall('./r_ele/re_pri')}
    for t in tags:
        if t.startswith('nf'):
            entry.add_tag(t)

    jiji_dict.add_entry(entry)


class JmdictReading:
    """Parse a english-jmdict reading(kana) into an object"""
    def __init__(self, xml_node):
        readings = [r.text for r in xml_node.findall('reb')]
        if len(readings) != 1:
            raise RuntimeError("JmdictKana with an invalid number of <reb>")
        self.text = readings[0]
        self.kanjis_restriction = {n.text for n in xml_node.findall('./re_restr')}


class JmdictSense:
    """Parse a english-jmdict sense into an object"""
    def __init__(self, xml_node):
        self.glosses = [g.text for g in xml_node.findall('gloss')]
        if not self.glosses:
            raise RuntimeError("JmdictSense without gloss")

        # Attach the sense to particular lemmas if specified
        self.lemmas_restriction = {n.text for n in xml_node.findall('./stagk')}
        self.readings_restriction = {n.text for n in xml_node.findall('./stagr')}

        # For words usually written in kana, add a lemma_restriction on kana forms
        self.is_usually_kana = any([misc.text == WRITTEN_WITH_KANA_PROP for misc in xml_node.findall('./misc')])

    def get_readings(self, all_readings):
        """Find the list of JmdictReading concerned by this sense"""
        if not self.readings_restriction and not self.lemmas_restriction:
            return all_readings

        sense_readings = set()
        if self.readings_restriction:
            sense_readings |= {r for r in all_readings if r.text in self.readings_restriction}
        if self.lemmas_restriction:
            sense_readings |= {r for r in all_readings if not r.kanjis_restriction or r.kanjis_restriction & self.lemmas_restriction}
        return sense_readings

    def has_restriction(self):
        return self.lemmas_restriction or self.readings_restriction


# Read the dictionary from JMDict export
read_dictionary()

# Add our custom tags
for tag_file_opts in TAGS_FILES_OPTS:
    if not isinstance(tag_file_opts, tuple):
        tag_file_opts = (tag_file_opts, {})
    jiji.tag_dictionary(jiji_dict, '../tags/' + tag_file_opts[0], **tag_file_opts[1])

# Export to jiji YAML format
jiji_dict.save('../../../dictionaries/japanese/jmdict_english.jiji.yaml')