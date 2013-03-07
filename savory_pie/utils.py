def camel_case(word):
    return ''.join([word.split('_')[0], ''.join(x.capitalize() for x in word.split('_')[1:])])
