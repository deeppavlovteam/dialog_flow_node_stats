import uuid
import random
import pathlib

import tqdm

from dff import GRAPH, RESPONSE, TRANSITIONS
from dff import Context, Actor

import dff_node_stats

stats_file = pathlib.Path("examples/stats.csv")
if stats_file.exists():
    stats_file.unlink()

# a dialog script
flows = {
    "root": {
        GRAPH: {
            "start": {
                RESPONSE: "Hi",
                TRANSITIONS: {
                    ("small_talk", "ask_some_questions"): "hi",
                    ("animals", "have_pets"): "i like animals",
                    ("animals", "like_animals"): "let's talk about animals",
                    ("news", "what_news"): "let's talk about news",
                },
            },
            "fallback": {RESPONSE: "Oops"},
        },
    },
    "animals": {
        GRAPH: {
            "have_pets": {RESPONSE: "do you have pets?", TRANSITIONS: {"what_animal": "yes"}},
            "like_animals": {RESPONSE: "do you like it?", TRANSITIONS: {"what_animal": "yes "}},
            "what_animal": {
                RESPONSE: "what animals do you have?",
                TRANSITIONS: {"ask_about_color": "bird", "ask_about_breed": "dog"},
            },
            "ask_about_color": {RESPONSE: "what color is it"},
            "ask_about_breed": {
                RESPONSE: "what is this breed?",
                TRANSITIONS: {
                    "ask_about_breed": "pereat",
                    "tell_fact_about_breed": "bulldog",
                    "ask_about_training": "i do not known",
                },
            },
            "tell_fact_about_breed": {
                RESPONSE: "Bulldogs appeared in England as specialized bull-baiting dogs. ",
            },
            "ask_about_training": {RESPONSE: "Do you train your dog? "},
        },
    },
    "news": {
        GRAPH: {
            "what_news": {
                RESPONSE: "what kind of news do you prefer?",
                TRANSITIONS: {"ask_about_science": "science ", "ask_about_sport": "sport "},
            },
            "ask_about_science": {
                RESPONSE: "i got news about science, do you want to hear?",
                TRANSITIONS: {
                    "science_news": "yes",
                    ("small_talk", "ask_some_questions"): "let's change the topic",
                },
            },
            "science_news": {
                RESPONSE: "This is science news",
                TRANSITIONS: {
                    "what_news": "ok",
                    ("small_talk", "ask_some_questions"): "let's change the topic",
                },
            },
            "ask_about_sport": {
                RESPONSE: "i got news about sport, do you want to hear?",
                TRANSITIONS: {
                    "sport_news": "yes",
                    ("small_talk", "ask_some_questions"): "let's change the topic",
                },
            },
            "sport_news": {
                RESPONSE: "This is sport news",
                TRANSITIONS: {
                    "what_news": "ok",
                    ("small_talk", "ask_some_questions"): "let's change the topic",
                },
            },
        },
    },
    "small_talk": {
        GRAPH: {
            "ask_some_questions": {
                RESPONSE: "how are you",
                TRANSITIONS: {
                    "ask_talk_about": "fine",
                    ("animals", "like_animals"): "let's talk about animals",
                    ("news", "what_news"): "let's talk about news",
                },
            },
            "ask_talk_about": {
                RESPONSE: "what do you want to talk about",
                TRANSITIONS: {
                    ("animals", "like_animals"): "dog",
                    ("news", "what_news"): "let's talk about news",
                },
            },
        },
    },
}

actor = Actor(flows, start_node_label=("root", "start"), fallback_node_label=("root", "fallback"))
stats = dff_node_stats.Stats(csv_file=stats_file)
stats.update_actor(actor, auto_save=False)
ctxs = {}
for i in tqdm.tqdm(range(1000)):
    for j in range(4):
        ctx = ctxs.get(j, Context(id=uuid.uuid4()))
        flow, node = ctx.node_label_history.get(ctx.previous_history_index, ["root", "fallback"])
        if [flow, node] == ["root", "fallback"]:
            ctx = Context()
            flow, node = ["root", "start"]
        answers = list(flows[flow][GRAPH][node].get(TRANSITIONS, {}).values())
        in_text = random.choice(answers) if answers else "go to fallback"
        ctx.add_human_utterance(in_text)
        ctx = actor(ctx)
        ctx.clear(hold_last_n_indexes=3)
        ctxs[j] = ctx
    if i % 50 == 0:
        stats.save()
