import csv
from statistics import median

from tools.language_level import get_language_level

"""
This script process the U of Haute Savoie frequency list, and output 12 lists of words
grouped by language level to be able to later tag the corresponding entries in jiji dictionaries
"""

TSV_FILE_PATH = './Lexique382.tsv'
TAGS_DIRECTORY_PATH = '../tags'
STOPWORDS_TAG_FILE = 'stopword.txt'

RANK_LAST = 1000000


# Read Japanese stopwords into a python dictionary
stopwords = {}
with open(f"{TAGS_DIRECTORY_PATH}/{STOPWORDS_TAG_FILE}") as f:
    for l in f.readlines():
        stopwords[l.strip()] = True


def offset_stopword(rank, nb_lemmas_in_stopwords):
    """Offset word frequency rankings by a small amount to take into account the missing ranks from ignored stopwords"""
    return max(1, rank - nb_lemmas_in_stopwords)


def read_lexique():
    """Read word frequency TSV file"""
    lists = dict()
    lemmas_freq = []
    nb_lemmas_in_stopwords = 0
    with open(TSV_FILE_PATH, newline='', encoding='utf-8') as freq_file:
        tsv_in = csv.reader(freq_file, delimiter='\t')
        next(tsv_in)  # Skip headers row
        for row in tsv_in:
            # row => 1_ortho	2_phon	3_lemme	4_cgram	5_genre	6_nombre	7_freqlemfilms2	8_freqlemlivres	9_freqfilms2	10_freqlivres...
            lemma = row[2]

            freqlemfilms2 = row[6].strip()
            freqlemlivres = row[7].strip()

            islem = bool(int(row[13]))

            if not islem:
                # skip entries that are not lemma(conjugated forms, etc...)
                continue

            # Ignore lemmas in the stopword list(very very frequent lemmas used for grammar)
            if lemma in stopwords:
                nb_lemmas_in_stopwords += 1
                continue

            if not freqlemfilms2 and not freqlemlivres:
                continue
            elif not freqlemfilms2:
                overall_freq = float(freqlemlivres)
            elif not freqlemlivres:
                overall_freq = float(freqlemfilms2)
            else:
                overall_freq = (2 * float(freqlemfilms2) + float(freqlemlivres)) / 3

            lemmas_freq.append((lemma, overall_freq))

    rank = 0
    lemmas_freq.sort(key=lambda lf: -lf[1])
    for lemma, freq in lemmas_freq:
        rank += 1
        lang_level = get_language_level(rank)
        if lang_level not in lists:
            lists[lang_level] = []
        lists[lang_level].append(lemma)

    return lists


lemmas_by_lang_level = read_lexique()


# Write frequency lists in tags/ folder
for lang_level, lemmas in lemmas_by_lang_level.items():
    if lang_level == 13:
        # Language level 13 contains very infrequent words that should be ignored
        continue
    with open(f"{TAGS_DIRECTORY_PATH}/freq{lang_level:02}.txt", 'w') as out:
        out.write('\n'.join(sorted(set(lemmas))))
