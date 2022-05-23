from base_classes.ArticleMetadata import ArticleMetadata
from default_modules.DefaultListCreator import ArticleOrder, DefaultListCreator
from custom_modules.TtrssCollector import TtrssCollector
import unittest
import unittest.mock as mock

class TestDefaultListCreator(unittest.TestCase):
    def test_should_include_article(self):
        article = ArticleMetadata("TITLE","URL","SOURCE")
        # if max_per_source_id is -1
        inst = DefaultListCreator([])
        self.assertTrue(inst._should_include_article(article,{}))
        # if max_per_source_id is 0
        inst = DefaultListCreator([], max_per_source_id=0)
        self.assertFalse(inst._should_include_article(article,{}))
        # if max_per_source_id is 1
        inst = DefaultListCreator([], max_per_source_id=1)
        self.assertTrue(inst._should_include_article(article,{}))
        self.assertFalse(inst._should_include_article(article,{"SOURCE":1}))
    
    def test_filter_collector_articles(self):
        collector = TtrssCollector("API")
        article1 = ArticleMetadata("TITLE1","URL","SOURCE")
        article2 = ArticleMetadata("TITLE2","URL","SOURCE")
        article3 = ArticleMetadata("TITLE3","URL","SOURCE1")
        article4 = ArticleMetadata("TITLE4","URL","SOURCE")
        collector.get_article_metadatas = mock.MagicMock(return_value=[
            article1, article2, article3, article4])
        collector2 = TtrssCollector("API")
        article5 = ArticleMetadata("TITLE5","URL","SOURCE")
        article6 = ArticleMetadata("TITLE6","URL","SOURCE")
        article7 = ArticleMetadata("TITLE7","URL","SOURCE1")
        article8 = ArticleMetadata("TITLE8","URL","SOURCE")
        collector2.get_article_metadatas = mock.MagicMock(return_value=[
            article5, article6, article7, article8])
        inst = DefaultListCreator([collector, collector2], max_per_source_id=1)
        articles = inst._filter_collector_articles()
        self.assertDictEqual(articles, {
                0:[article1, article3],
                1:[article5, article7]
            }
        )
    
    def test_zip_collectors(self):
        article1 = ArticleMetadata("TITLE1","URL","SOURCE")
        article2 = ArticleMetadata("TITLE2","URL","SOURCE")
        article3 = ArticleMetadata("TITLE3","URL","SOURCE")
        article4 = ArticleMetadata("TITLE4","URL","SOURCE")
        article5 = ArticleMetadata("TITLE5","URL","SOURCE")
        article6 = ArticleMetadata("TITLE6","URL","SOURCE")
        article7 = ArticleMetadata("TITLE7","URL","SOURCE")
        article8 = ArticleMetadata("TITLE8","URL","SOURCE")

        # no max
        #   two collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API")])
        articles = inst.zip_collectors({
            0:[article1, article2, article3, article4],
            1:[article5, article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article5, article2, article6, article3, article7, article4, article8])
        #   three collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API"),TtrssCollector("API")])
        articles = inst.zip_collectors({
            0:[article1, article2, article3],
            1:[article4, article5],
            2:[article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article4, article6, article2, article5, article7, article3, article8])
        
        # max 4
        #   two collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API")], max_num_articles=4)
        articles = inst.zip_collectors({
            0:[article1, article2, article3, article4],
            1:[article5, article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article5, article2, article6])
        #   three collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API"),TtrssCollector("API")], max_num_articles=4)
        articles = inst.zip_collectors({
            0:[article1, article2, article3],
            1:[article4, article5],
            2: [article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article4, article6, article2])
   

    def test_in_order(self):
        article1 = ArticleMetadata("TITLE1","URL","SOURCE")
        article2 = ArticleMetadata("TITLE2","URL","SOURCE")
        article3 = ArticleMetadata("TITLE3","URL","SOURCE")
        article4 = ArticleMetadata("TITLE4","URL","SOURCE")
        article5 = ArticleMetadata("TITLE5","URL","SOURCE")
        article6 = ArticleMetadata("TITLE6","URL","SOURCE")
        article7 = ArticleMetadata("TITLE7","URL","SOURCE")
        article8 = ArticleMetadata("TITLE8","URL","SOURCE")

        # no max
        #   two collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API")])
        articles = inst.in_order({
            0:[article1, article2, article3, article4],
            1:[article5, article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article2, article3, article4, article5, article6, article7, article8])
        #   three collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API"),TtrssCollector("API")])
        articles = inst.in_order({
            0:[article1, article2, article3],
            1:[article4, article5],
            2:[article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article2, article3, article4, article5, article6, article7, article8])
        
        # max 4
        #   two collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API")], max_num_articles=4)
        articles = inst.in_order({
            0:[article1, article2, article3],
            1:[article5, article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article2, article3, article5])
        #   three collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API"),TtrssCollector("API")], max_num_articles=4)
        articles = inst.in_order({
            0:[article1],
            1:[article4, article5],
            2: [article6, article7, article8]
        })
        self.assertListEqual(articles, [article1, article4, article5, article6])

    def test_random_order(self):
        """
        You can't really test randomness, but we can test that we get all the articles we expect
            or at least get the number of articles that we expect and they're all unique
        """
        article1 = ArticleMetadata("TITLE1","URL","SOURCE")
        article2 = ArticleMetadata("TITLE2","URL","SOURCE")
        article3 = ArticleMetadata("TITLE3","URL","SOURCE")
        article4 = ArticleMetadata("TITLE4","URL","SOURCE")
        article5 = ArticleMetadata("TITLE5","URL","SOURCE")
        article6 = ArticleMetadata("TITLE6","URL","SOURCE")
        article7 = ArticleMetadata("TITLE7","URL","SOURCE")
        article8 = ArticleMetadata("TITLE8","URL","SOURCE")

        # no max
        #   two collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API")])
        articles = inst.random_order({
            0:[article1, article2, article3, article4],
            1:[article5, article6, article7, article8]
        })
        self.assertSetEqual(set(articles), {article1, article5, article2, article6, article3, article7, article4, article8})
        #   three collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API"),TtrssCollector("API")])
        articles = inst.random_order({
            0:[article1, article2, article3],
            1:[article4, article5],
            2:[article6, article7, article8]
        })
        self.assertSetEqual(set(articles), {article1, article5, article2, article6, article3, article7, article4, article8})
        
        # max 4
        #   two collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API")], max_num_articles=4)
        articles = inst.random_order({
            0:[article1, article2, article3, article4],
            1:[article5, article6, article7, article8]
        })
        self.assertEqual(len(set(articles)), 4) # contains 4 unique items

        #   three collectors
        inst = DefaultListCreator([TtrssCollector("API"),TtrssCollector("API"),TtrssCollector("API")], max_num_articles=4)
        articles = inst.random_order({
            0:[article1, article2, article3],
            1:[article4, article5],
            2: [article6, article7, article8]
        })
        self.assertEqual(len(set(articles)), 4) # contains 4 unique items

    def test_callback_collectors(self):
        # filters out the articles that aren't relevant to this collector
        article1 = ArticleMetadata("TITLE1","URL","SOURCE")
        article1.set_collector_id('0')
        article2 = ArticleMetadata("TITLE2","URL","SOURCE")
        article2.set_collector_id('0')
        article3 = ArticleMetadata("TITLE3","URL","SOURCE")
        article3.set_collector_id('1')
        article4 = ArticleMetadata("TITLE4","URL","SOURCE")
        article4.set_collector_id('2')
        collector1 = TtrssCollector("API")
        collector1.used_articles_callback = mock.MagicMock()
        collector2 = TtrssCollector("API")
        collector2.used_articles_callback = mock.MagicMock()
        collector3 = TtrssCollector("API")
        collector3.used_articles_callback = mock.MagicMock()
        
        inst = DefaultListCreator([collector1,collector2,collector3])
        inst.callback_collectors([article1,article2,article3,article4])
        collector1.used_articles_callback.assert_called_with([article1,article2])
        collector2.used_articles_callback.assert_called_with([article3])
        collector3.used_articles_callback.assert_called_with([article4])

    def get_article_metadatas(self):
        collector = TtrssCollector("API")
        article1 = ArticleMetadata("TITLE1","URL","SOURCE")
        article2 = ArticleMetadata("TITLE2","URL","SOURCE")
        article3 = ArticleMetadata("TITLE3","URL","SOURCE")
        article4 = ArticleMetadata("TITLE4","URL","SOURCE")
        collector.get_article_metadatas = mock.MagicMock(return_value=[
            article1, article2, article3, article4])
        collector.used_articles_callback = mock.MagicMock()

        collector2 = TtrssCollector("API")
        article5 = ArticleMetadata("TITLE5","URL","SOURCE")
        article6 = ArticleMetadata("TITLE6","URL","SOURCE")
        article7 = ArticleMetadata("TITLE7","URL","SOURCE")
        article8 = ArticleMetadata("TITLE8","URL","SOURCE")
        collector2.get_article_metadatas = mock.MagicMock(return_value=[
            article5, article6, article7, article8])
        collector2.used_articles_callback = mock.MagicMock()

        inst = DefaultListCreator([collector, collector2],ArticleOrder.IN_ORDER, max_num_articles=3, max_per_source_id=1)
        articles = inst.get_article_metadatas()
        # calls the callback if desired
        collector.used_articles_callback.assert_called_once_with([article1])
        collector2.used_articles_callback.assert_called_once_with([article5])
        # returns the right metadata in the right order
        self.assertListEqual(articles, [article1, article5])

        inst = DefaultListCreator([collector, collector2],ArticleOrder.IN_ORDER, max_num_articles=5, max_per_source_id=2)
        articles = inst.get_article_metadatas()
        # calls the callback if desired
        collector.used_articles_callback.assert_called_once_with([article1, article2])
        collector2.used_articles_callback.assert_called_once_with([article5, article6])
        # returns the right metadata in the right order
        self.assertListEqual(articles, [article1, article2, article5, article6])
