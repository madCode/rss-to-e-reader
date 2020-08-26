from article import words_per_minute

def get_table_of_contents(articles):
    total_word_count = 0
    results = []
    for article in articles:
        results.append(f'<li>({words_per_minute(article.word_count)}) <a href="#{article.id}">{article.title}</a></li>')
        total_word_count += article.word_count
    results.insert(0, f'<h1 id="top">Table of Contents (Total Read Time: {words_per_minute(total_word_count)})</h1><ol>')
    results.append('</ol>')
    return "".join(results)

def next_id(articles, index):
    if index + 1 >= len(articles):
        return 'top'
    else:
        return articles[index+1].id

def create_file(articles, filestub):
    file = open(filestub +'.html', "w+")
    file.write(f'<html><head><title>{filestub}</title></head><body>')
    file.write(get_table_of_contents(articles))
    total = len(articles)
    i = 0
    for article in articles:
        file.write(article.toHtmlString(next_id(articles, i)))
        if i%10 == 0:
            print(f'writing article {i}/{total}')
        i += 1
    file.write('</body></html>')
    file.close()