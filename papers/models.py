from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    #papers = models.ManyToManyField(Paper, related_name='tags') 

    #def __str__(self):
    #    return self.name

class LdaModel(models.Model):
    # Assuming you want to store metadata about the model itself
    # For example, you might want to store the number of topics
    num_topics = models.IntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    # Any other fields relevant to the LDA model itself

class Topic(models.Model):
    lda_model = models.ForeignKey(LdaModel, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=255)
    # You could also add fields for storing topic keywords, coherence scores, etc.


class Paper(models.Model):
    pmid = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    authors = models.TextField()  # Store authors as a comma-separated list
    year = models.IntegerField(null=True, blank=True)
    journal = models.CharField(max_length=255)
    doi = models.CharField(max_length=100, unique=True, null=True, blank=True)
    abstract = models.TextField(null=True, blank=True)  # Some papers might not have an abstract
    categories = models.ManyToManyField(Tag, related_name='papers')
    factor = models.FloatField(null=True, blank=True)
    citations = models.IntegerField(null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')


    def __str__(self):
        return self.title



class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    papers = models.ManyToManyField(Paper, related_name='groups')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_groups')

    def __str__(self):
        return self.name
