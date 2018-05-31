import csv
from statistics import median

from tools.language_level import get_language_level

"""
This script process the BCCWJ japanese words frequency list, and output 12 lists of words
grouped by language level to be able to later tag the corresponding entries in jiji dictionaries
Note there are two frequency lists, based on short unit words(suw) and long unit words(luw)
for our purpose it's better to use the short unit words version.
"""

BCCWJ_TSV_FILE_PATH = './BCCWJ_frequencylist_suw_ver1_0.tsv'
TAGS_DIRECTORY_PATH = '../tags'
STOPWORDS_TAG_FILE = 'stopword.txt'
FREQ01_EXPRESSIONS_FILE = 'frequent_expressions01.txt'
FREQ02_EXPRESSIONS_FILE = 'frequent_expressions02.txt'
RANK_LAST = 1000000


# Read Japanese stopwords into a python dictionary
stopwords = {}
with open(f"{TAGS_DIRECTORY_PATH}/{STOPWORDS_TAG_FILE}") as f:
    for l in f.readlines():
        stopwords[l.strip()] = True


def offset_stopword(rank):
    """Offset word frequency rankings by a small amount to take into account the missing ranks from ignored stopwords"""
    return max(1, rank - 250)


def add_frequent_expressions(file_path, lang_level):
    """Add frequent expression to frequency lists
    This is to fix very frequent expressions that do not appear in bccwj because
    they are parsed differently. Ex: 確かに / 確か|に
    """
    with open(file_path) as f:
        for l in f.readlines():
            if l.strip() and not l.strip().startswith('#'):
                lemmas_by_lang_level[lang_level].append(l.strip())


def read_bccwj():
    """Read word frequency TSV file"""
    lists = dict()
    with open(BCCWJ_TSV_FILE_PATH, newline='', encoding='utf-8') as freq_file:
        tsv_in = csv.reader(freq_file, delimiter='\t')
        next(tsv_in)  # Skip headers row
        for row in tsv_in:
            # row => rank	lForm	lemma	pos	subLemma	wType	frequency	pmw	PB_rank	PB_frequency	PB_pmw...
            lemma = row[2]

            if '■' in lemma:
                # some entries are broken, with unicode black square in the lemma, skip them
                continue

            # Ignore lemmas in the stopword list(very very frequent lemmas used for grammar)
            if lemma in stopwords:
                continue

            overall_rank = int(row[0])
            magazines_rank = int(row[11]) if row[12] else RANK_LAST
            manuals_rank = int(row[23]) if row[23] else RANK_LAST
            chiebukuro_rank = int(row[32]) if row[32] else RANK_LAST
            blogs_rank = int(row[35]) if row[35] else RANK_LAST

            lang_level = int(median([
                get_language_level(offset_stopword(overall_rank)),
                # get_language_level(offset_stopword(manuals_rank)),
                get_language_level(offset_stopword(magazines_rank)),
                get_language_level(offset_stopword(chiebukuro_rank)),
                get_language_level(offset_stopword(blogs_rank))
            ]))

            if lang_level not in lists:
                lists[lang_level] = []
            lists[lang_level].append(lemma)

    return lists


lemmas_by_lang_level = read_bccwj()
add_frequent_expressions(FREQ01_EXPRESSIONS_FILE, 1)
add_frequent_expressions(FREQ02_EXPRESSIONS_FILE, 2)

# Write frequency lists in tags/ folder
for lang_level, lemmas in lemmas_by_lang_level.items():
    if lang_level == 13:
        # Language level 13 contains very infrequent words that should be ignored
        continue
    with open(f"{TAGS_DIRECTORY_PATH}/freq{lang_level:02}.txt", 'w') as out:
        out.write('\n'.join(sorted(set(lemmas))))
