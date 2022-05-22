import unittest
from ArticleMetadata import ArticleMetadata

from article import Article

class TestArticle(unittest.TestCase):
    def test_word_count(self):
        a = """
            had not long to wait before making further acquaintance with my pretty midnight visitor.  Our second meeting took place within a few hours of the police call and on the same day.  I had been out for a long walk across the hills and was tramping steadily along the high road towards Stone Hollow, when I saw, gleaming through the darkness—it was already dark though only late afternoon—at probably the loneliest and most desolate spot in the Dale, the headlights of a motor-car evidently at a standstill.

            “It's a weird place for a halt and worse if it's a breakdown,” I murmured, and involuntarily quickened my steps.

            But as I approached the car I saw a moving light and then the shadow of a woman walking towards me, carrying, apparently, a small electric torch.  Evidently she had heard my approach and had set out to meet me.  As she stepped momentarily into the light of the car p. 35I recognised her.  It was the girl of the midnight visit.

            “Who is it, Kitty?” demanded a quick, imperious voice somewhere in the darkness.  “Tell him to come here.  Do you know him?”

            “Lady Clevedon is in the car,” the girl said a little hurriedly.  “Will you come and speak to her?”

            “Is it a breakdown?” I queried.

            “No,” the girl responded, “it is Hartrey.  We have lost him.”

            But I had no immediate opportunity of questioning her as to the missing Hartrey, or the manner of his going, for “Kitty,” as the old lady had addressed her, had run to the door of the car and pulled it open, to reveal old Lady Clevedon, white of hair, very erect of figure, rather stern of face and with keen, searching eyes that just now were full of wrath.

            “Is there anything I can do?” I began.

            “You can find Hartrey,” her ladyship responded, not exactly snappily, but quite ungently; she was evidently used to giving orders, and it never occurred to her, apparently, that I would do any other than obey.

            “Who is Hartrey?” I demanded.

            “He is the chauffeur,” the girl explained. p. 36“We sent him with a message to Lepley's farm—it is over there.”

            She pointed vaguely into the darkness, and I followed her gesture with my eyes.  But I could see no sign of house or light or living creature—only the darkness and, in the fore-ground, the blurred outlines of masses of rock.
        """
        A = Article(ArticleMetadata("","",""),display_content=a)
        self.assertEqual(A.word_count,404)