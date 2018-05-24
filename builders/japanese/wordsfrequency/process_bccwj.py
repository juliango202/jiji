
import sys
import csv
import yaml
import xml.etree.ElementTree as etree
from collections import OrderedDict


# This script process the BCCWJ japanese words frequency list, and the JMDict XML file 
# and output jiji dictionary data in TSV format
# See http://www.edrdg.org/jmdict/jmdict_dtd_h.html for JMDict DTD
# ----------------------------------------------------------------
# Here is a sample entry for JMdict XML format
#
# <entry>
#     <ent_seq>1000110</ent_seq>
#     <k_ele>
#         <keb>ＣＤプレーヤー</keb>
#         <ke_pri>spec1</ke_pri>
#     </k_ele>
#     <k_ele>
#         <keb>ＣＤプレイヤー</keb>
#     </k_ele>
#     <r_ele>
#         <reb>シーディープレーヤー</reb>
#         <re_restr>ＣＤプレーヤー</re_restr>
#         <re_pri>spec1</re_pri>
#     </r_ele>
#     <r_ele>
#         <reb>シーディープレイヤー</reb>
#         <re_restr>ＣＤプレイヤー</re_restr>
#     </r_ele>
#     <sense>
#         <pos>&n;</pos>
#         <gloss>CD player</gloss>
#     </sense>
#     <sense>
#         <gloss>audio player</gloss>
#         <gloss>audio CD player</gloss>
#     </sense>
# </entry>
#
# We want to keep the word kanji forms(<keb> tag), kana forms(<reb> tag), and meaning(<sense> tag)


if len(sys.argv) < 3:
    print("Usage: {} <bccwj-file> <english-jmdict-file>".format(sys.argv[0]))
    sys.exit()

LANG_LEVEL_LIMITS = [0,700,1500,2500,4000,7000,12000,20000,32000,64000,128000,256000]
#LANG_LEVEL_LIMITS = [0,2093,4187,8375,16751,33503,67006,134012,268024,402036]


# Read word frequency TSV file
freqByKana = dict()
freqByKanji = dict()
with open(sys.argv[1], newline='', encoding='utf-8') as freq_file:
    tsvin = csv.reader(freq_file, delimiter='\t')
    next(tsvin) # Skip headers row
    for row in tsvin:
        #row => rank   lForm   lemma   pos subLemma    wType   frequency   pmw PB_rank PB_frequency    PB_pmw  PM_rank PM_frequency
        if '■' in row[2]:
            # some entries are broken, with unicode black square in the lemma, skip them
            continue
        rank = int(row[0])
        # Language level => 10 levels from frequently used to rarely used(exponential nb of words)
        lang_level = 0
        for idx, limit in enumerate(LANG_LEVEL_LIMITS):
            if rank > limit:
                lang_level = idx + 1
        freqByKana[row[1]] = lang_level if row[1] not in freqByKana else min(lang_level, freqByKana[row[1]])
        freqByKanji[row[2]] = lang_level if row[2] not in freqByKanji else min(lang_level, freqByKanji[row[2]])

# Construc Jiji dictionary object
jiji = OrderedDict()
jiji['title'] = 'Jim\'s Breen Japanese dictionary'
jiji['licence'] = ''
jiji['languages'] = OrderedDict([('from', 'Japanese'),('to', 'English')])

# Read dictionary 
tree = etree.parse(sys.argv[2])
root = tree.getroot()    

# TSV column names
#print("{}\t{}\t{}\t{}".format('entry', 'lemma', 'frequency', 'english'))

# Loop through the dictionary entries
jiji_entries = {}
for entry in root:
    entryNumber = entry.find('ent_seq').text
    
    #for k in entry.findall('./k_ele/keb'):
        #print(etree.tostring(k, encoding='utf8', method='xml'))
    kanjiForms = [] if entry.find('./k_ele/keb') is None else [k.text for k in entry.findall('./k_ele/keb')]    
    kanaForms  = [] if entry.find('./r_ele/reb') is None else [k.text for k in entry.findall('./r_ele/reb')]    
    
    jijiForms = kanjiForms
    if not kanjiForms or any([misc.text == 'word usually written using kana alone' for misc in entry.findall('./sense/misc')]):
        jijiForms = kanaForms + jijiForms
        if not kanjiForms:
            kanaForms = []
    
    senses = []
    for sense in entry.findall('sense'):
        glosses = [g.text for g in sense.findall('gloss')] 
        if glosses:
            senses.append('/'.join(glosses).replace('\n', ''))
        
    if not senses:
        print("ERROR: Entry {} has no meaning defined, will skip.".format(entryNumber), file=sys.stderr)
        continue
        
    ranks = []
    for f in jijiForms:
        if f in freqByKanji:
            ranks.append(freqByKanji[f])
    if not ranks:       
        for f in jijiForms:
            if f in freqByKana:
                ranks.append(freqByKana[f])

    entryLemmas = ', '.join(jijiForms)
    entry = OrderedDict()
    if len(senses) == 1:
        entry['sense'] = senses[0]
    else:
        entry['senses'] = senses

    if ranks:
        entry["frequency"] = min(ranks)
        
    if kanaForms:
        entry["pronunciation"] = ", ".join(kanaForms)
        
    if entryLemmas in jiji_entries:
        #print("ERROR: Entry {} lemmas {} already exists, will skip.".format(entryNumber, entryLemmas), file=sys.stderr)
        continue
    
    jiji_entries[entryLemmas] = entry
    
    
# Somehow yaml needs some strange initialization to work with OrderedDict
# See https://stackoverflow.com/a/31609484/257272
def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(OrderedDict, represent_dict_order)    
setup_yaml()


# Print JIJI dictionary infos
print(yaml.dump({"about_this_dictionary": jiji}, default_flow_style=False, allow_unicode=True), end='')

print(yaml.dump(jiji_entries, default_flow_style=False, allow_unicode=True))

