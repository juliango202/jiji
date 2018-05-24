"""
We want to categorize the words/lemmas of a language in 12 levels, from the most frequently used to the rarely used.
An additional level 13 contains words/lemmas with a frequency ranking > 50000 that should be ignored
because at this level they are probably not significant.
The number of words in each level was chosen to take into account that:
- 1000 words allow you to understand about 80% of the language which surrounds you
- 3000 words allow you to understand about 95% of most ordinary texts
- 5000 words allow you to understand about 98% of most ordinary texts
- 10000 words allow you to understand about 99% of most texts
From Nation (1990) and Laufer (1997)
"""
LANG_LEVEL_LIMITS = [0,400,1000,1800,2800,4000,5500,7500,10000,14000,20000,30000, 50000]


def get_language_level(word_rank):
    """Compute the language level of a word according to its frequency ranking"""
    word_lang_level = 0
    for idx, limit in enumerate(LANG_LEVEL_LIMITS):
        if word_rank > limit:
            word_lang_level = idx + 1
    return word_lang_level
