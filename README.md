## A YAML syntax for storing language dictionaries

_a paper dictionary in a text file..._

Compared with other current dictionary formats([DICT](https://en.wikipedia.org/wiki/DICT),
[TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/DI.html),
[slob](https://github.com/itkach/slob)) the goal is to have something that is really
simple to understand and modify by end users, in the tradition of open source software.
Ideally it should read like a paper dictionary in a text file, with the YAML syntax
just used for automatic parsing.

Because YAML is ubiquitous, it's also easy to use and implement for developers.

## Format description

Each entry in the dictionary is introduced by one or more lemma separated by a comma(several
lemmas are necessary when the word can be written in several ways). The entry must have a `sense`
property with the sense/meaning of the word, or a `senses` property containing a list of senses.

Other properties are optional:
- `pronunciation`: one or more pronunciation of the words/lemmas, separated by a comma
- `tags`: one or more tag for the entry, separated by a comma

### Examples

```yaml
manifestación:
  sense: demonstration
manifestante:
  sense: demonstrator
manifestar:
  sense: manifest
```
```yaml
家猫:
  sense: domesticated cat
  pronunciation: いえねこ, イエネコ
うなり声, 唸り声:
  senses:
  - groan/moan
  - roar/growl
  - buzz/hum (e.g. motor)/whistling (e.g. wind, wires in the wind)
  pronunciation: うなりごえ
ローンチ, ロンチ, ラーンチ, ラウンチ, ランチ:
  sense: launch
  tags: jlpt2
```

### Dictionary information

A special entry called `_about_this_dictionary` is used to store the information about the dictionary itself,
including the title, licence, and the language(s) used.
```yaml
_about_this_dictionary:
  title: Jim's Breen Japanese dictionary
  licence: Creative Commons Attribution-ShareAlike Licence (V3.0)
  languages:
    from: Japanese
    to: English
```

## TODO:
Add more builders:
- Use wiktionary parser => https://github.com/juditacs/wikt2dict
- from wikdict http://download.wikdict.com/dictionaries/sqlite/2_2017-11/ (why spanish "acaudalado" is not defined ?)
