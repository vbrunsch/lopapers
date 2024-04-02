import gensim
import os
import json
import re
import nltk
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis
import gensim
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from gensim import corpora, models
from gensim.models import CoherenceModel
from collections import defaultdict
from gensim.corpora import Dictionary
from gensim.models import LdaModel as GensimLdaModel
from .models import Paper, Topic, LdaModel
from django.utils import timezone
from django.conf import settings

def run_lda_clustering():
    print("Starting LDA clustering process...")
    papers = Paper.objects.all()
    
    # Create and save the LdaModel instance
    #lda_model_instance = LdaModel(date_created=timezone.now())
    #lda_model_instance.save()
    
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

    # Initialize a lemmatizer
    lemmatizer = WordNetLemmatizer()
    
    
    # Define a function to clean and tokenize abstracts
    def preprocess_abstract(abstract):
        
        # Convert to lowercase
        text = abstract.lower()
        # Remove non-alphanumeric characters, except for hyphens in words like "covid-19"
        text = re.sub(r'\b\d+\b', ' ', text)  # Remove standalone numbers
        text = re.sub(r'\W+', ' ', text)  # Remove non-word characters except for hyphens in words
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords
        tokens = [word for word in tokens if word not in stopwords.words('english')]
        # Lemmatize tokens
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        return tokens

    # Preprocess all abstracts
    processed_abstracts = [preprocess_abstract(paper.abstract) for paper in papers]

    # Count how many documents each word appears in
    doc_frequency = defaultdict(int)
    for tokens in processed_abstracts:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_frequency[token] += 1

    # Calculate the threshold for high-frequency words (e.g., words appearing in more than 90% of documents)
    num_documents = len(processed_abstracts)
    threshold = num_documents * 0.9

    # Identify high-frequency words
    high_freq_words = {word for word, freq in doc_frequency.items() if freq > threshold}

    # Update the preprocessing function to exclude high-frequency words
    def preprocess_abstract_updated(abstract):
        tokens = preprocess_abstract(abstract)
        # Exclude high-frequency words
        tokens = [token for token in tokens if token not in high_freq_words]
        return tokens

    # Preprocess abstracts again, excluding high-frequency words
    processed_abstracts_updated = [preprocess_abstract_updated(paper.abstract) for paper in papers]

    # Assuming 'processed_abstracts' is your list of documents, where each document is a list of words
    documents = processed_abstracts_updated

    # Step 1: Prepare the dictionary and corpus
    dictionary = corpora.Dictionary(documents)
    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # Step 2: Train the LDA model
    #lda_model = models.LdaModel(corpus, num_topics=10, id2word=dictionary, passes=15)

    # Step 3: Explore the topics
    #coherence_model_lda = CoherenceModel(model=lda_model, texts=documents, dictionary=dictionary, coherence='c_v')
    #coherence_lda = coherence_model_lda.get_coherence()
    #print('\nCoherence Score: ', coherence_lda)

    # Exploring the optimal number of topics
    # Define a range for the number of topics
    min_topics = 2
    max_topics = 8
    step_size = 1
    topics_range = range(min_topics, max_topics + 1, step_size)

    # List for coherence values
    coherence_values = []

    for num_topics in topics_range:
        print(f"Training model with {num_topics} topics")
        model = models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=15)
        coherencemodel = CoherenceModel(model=model, texts=documents, dictionary=dictionary, coherence='c_v')
        coherence_values.append(coherencemodel.get_coherence())
        print(f"Processed {num_topics} topics, coherence: {coherencemodel.get_coherence()}")


    # Find the number of topics with the highest coherence score
    optimal_topic_number = topics_range[coherence_values.index(max(coherence_values))]
    print(f"Optimal number of topics: {optimal_topic_number}, Coherence score: {max(coherence_values)}")

    # Re-train the model with the optimal number of topics
    lda_model_optimal = models.LdaModel(corpus, num_topics=optimal_topic_number, id2word=dictionary, passes=15)
    

    # Create and save the LdaModel instance with the optimal number of topics
    lda_model_instance = LdaModel(date_created=timezone.now(), num_topics=optimal_topic_number)
    print(f"Saving LdaModel instance with {lda_model_instance.num_topics} topics.")

    lda_model_instance.save()

    # Proceed with creating Topic instances and other operations
    for topic_num in range(optimal_topic_number):
        # Extracting the top keywords for each topic
        topic_keywords = lda_model_optimal.show_topic(topic_num, topn=5)
        topic_keywords_str = ", ".join([word for word, _ in topic_keywords])
        
        # Creating a Topic instance for each topic
        topic_instance = Topic(name=f"Topic {topic_num + 1}", lda_model=lda_model_instance)
        topic_instance.save()


    # Assign papers to topics using lda_model_optimal
    for i, bow in enumerate(corpus):
        paper = papers[i]  # Assuming papers and corpus are directly correlated
        topics_distribution = lda_model_optimal.get_document_topics(bow)
        dominant_topic = max(topics_distribution, key=lambda x: x[1])[0]
        topic_instance = Topic.objects.get(name=f"Topic {dominant_topic + 1}", lda_model=lda_model_instance)
        paper.topic = topic_instance
        paper.save()

    #dominant_topics = []
    #for i, row in enumerate(lda_model_optimal[corpus]):
    #    row = sorted(row, key=lambda x: (x[1]), reverse=True)
    #    # Get the dominant topic, its percentage contribution, and keywords for each document
    #    for j, (topic_num, prop_topic) in enumerate(row):
    #        if j == 0:  # => dominant topic
    #            wp = lda_model_optimal.show_topic(topic_num)
    #            topic_keywords = ", ".join([word for word, prop in wp])
    #            dominant_topics.append((i, int(topic_num), round(prop_topic,4), topic_keywords))
    #        else:
    #            break

    # Step 2: Aggregate Papers by Dominant Topic
    #from collections import defaultdict
    #papers_by_topic = defaultdict(list)
    #for i, topic_info in enumerate(dominant_topics):
    #    topic_num = topic_info[1]
    #    papers_by_topic[topic_num].append(i)  # assuming 'i' is a unique identifier for each paper

   

        
    # Using the top N keywords of each topic as its "name"
    #topic_names = {}
    #N = 3
    #for topic_num in range(lda_model_optimal.num_topics):
    #    wp = lda_model_optimal.show_topic(topic_num, topn=N)
    #    topic_keywords = ", ".join([word for word, prop in wp])
    #    topic_names[topic_num] = topic_keywords

    # Print each topic name and the count of papers assigned to that topic
    #for topic_num, papers in papers_by_topic.items():
    #    print(f"Topic {topic_num + 1}: {topic_names[topic_num]}")
    #    print(f"Number of papers grouped to this topic: {len(papers)}\n")

    # Now 'papers_by_topic' contains papers grouped by their dominant topic
    # And 'topic_names' contains a potential name for each topic based on its top N keywords
        
    # Preparing the visualization
    #pyLDAvis.enable_notebook()
    vis = gensimvis.prepare(lda_model_optimal, corpus, dictionary)
    visualization_path = os.path.join(settings.MEDIA_ROOT, 'lda_visualization.html')
    pyLDAvis.save_html(vis, visualization_path)
    
    # Save the visualization to an HTML file
    pyLDAvis.save_html(vis, 'lda_visualization.html')
    


#if __name__ == '__main__':
#    nltk.download('punkt')
#    nltk.download('stopwords')
#    nltk.download('wordnet')
#    main()