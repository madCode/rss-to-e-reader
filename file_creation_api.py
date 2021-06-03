from unidecode import unidecode

from article import time_to_read_str

def get_table_of_contents(articles):
    total_word_count = 0
    results = []
    for article in articles:
        results.append(f'<li>({time_to_read_str(article.word_count)}) <a href="#{article.id}">{article.title}</a></li>')
        total_word_count += article.word_count
    results.insert(0, f'<h1 id="top">Table of Contents (Total Read Time: {time_to_read_str(total_word_count)})</h1><ol>')
    results.append('</ol>')
    return "".join(results)

def next_id(articles, index):
    if index + 1 >= len(articles):
        return 'top'
    else:
        return articles[index+1].id

def create_file(articles, filestub):
    file = open(filestub +'.html', "w+")
    content_html = f'<!DOCTYPE html><html lang="en"><head><title>{filestub}</title></head><body>'
    content_html += get_table_of_contents(articles)
    total = len(articles)
    i = 0
    for article in articles:
        content_html += article.toHtmlString(next_id(articles, i))
        if i%10 == 0:
            print(f'writing article {i}/{total}')
        i += 1
    content_html += '</body></html>'
    content_html = unidecode(content_html)
    file.write(content_html)
    file.close()
