import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from .models import Choice, Question


def create_question(question_text, days):
    """
    Create a question with given `question_text` and published the
    give number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet not published)
    """
    time = timezone.now() + datetime.timedelta(days = days)
    return Question.objects.create(question_text = question_text, pub_date = time)

class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days = 30)
        future_question = Question(pub_date = time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is old than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days = 30)
        old_question = Question(pub_date = time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() return True for question whose pub_date
        is within last day.
        """
        time = timezone.now() - datetime.timedelta(hours = 23, minutes = 59, seconds = 59)
        recent_question = Question(pub_date = time)
        self.assertIs(recent_question.was_published_recently(), True)

class QuestionIndexviewTests(TestCase):

    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context["latest_question_list"], [])

    def test_past_questions(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        create_question(question_text = "Past question.", days = -30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_future_questions(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text = "Future question.", days = 30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_and_past_questions(self):
        """
        Even if both past and future question exist, only past questions
        are displayed.
        """
        create_question(question_text = "Past question.", days = -30)
        create_question(question_text = "Future question.", days = 30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        create_question(question_text = "Past question 1.", days = -30)
        create_question(question_text = "Past question 2.", days = -5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )

class QuestionDetailViewTests(TestCase):
    def test_future_questions(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text = "Future question.", days = 5)
        url = reverse('polls:detail', args = (future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_questions(self):
        """
        The detail view of a question with a pub_date in the past
        display the question's text.
        """
        past_question = create_question(question_text = "Past question.", days = -5)
        url = reverse('polls:detail', args = (past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

class VoteViewTests(TestCase):
    def test_vote_not_exist_questions(self):
        """
        The vote view of a question not exist
        returns a 404 not found.
        """
        url = reverse('polls:vote', args = (1,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_vote_not_exist_choices(self):
        """
        The vote view of a choice not exist
        display your didn't select a choice
        """
        question = create_question(question_text = 'No choice question.', days = -5)
        url = reverse('polls:vote', args = (question.id,))
        response = self.client.post(url)
        self.assertTemplateUsed(response, 'polls/detail.html')
        self.assertContains(response, escape("your didn't select a choice"))

    def test_vote_questions(self):
        """
        The vote view of a question
        display the 1 vote.
        """
        question = create_question(question_text = "One vote question.", days = -5)
        choice = Choice.objects.create(
            choice_text = "One vote choice.",
            question_id = question.id
        )
        url = reverse('polls:vote', args = (question.id,))
        response = self.client.post(url, {'choice': choice.id})
        self.assertRedirects(response, reverse('polls:results', args=(question.id,)))

class ResultsViewTests(TestCase):
    def test_not_exist_questions(self):
        """
        The results view of a question not exist
        returns a 404 not found.
        """
        url = reverse('polls:results', args = (1,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_choice_questions(self):
        """
        The results view of a question without choice
        display the question's text.
        """
        question = create_question(question_text = "No choice question.", days = -5)
        url = reverse('polls:results', args = (question.id,))
        response = self.client.get(url)
        self.assertContains(response, "No choice question.")

    def test_one_choice_questions(self):
        """
        The results view of a quesiton with one choice
        display the choice_text.
        """
        question = create_question(question_text = "One choice question.", days = -5)
        Choice.objects.create(choice_text = "Choice text.", question_id = question.id)
        url = reverse('polls:results', args = (question.id,))
        response = self.client.get(url)
        self.assertContains(response, "Choice text.")

    def test_one_vote_choice_question(self):
        """
        The results view of a question with one vote
        display the 1 vote.
        """
        question = create_question(question_text = "One vote question.", days = -5)
        Choice.objects.create(
            choice_text = "One vote choice.",
            question_id = question.id,
            votes = 1
        )
        url = reverse('polls:results', args = (question.id,))
        response = self.client.get(url)
        self.assertContains(response, "1 vote")
