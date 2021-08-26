import uuid
import random
import pathlib

import tqdm

from dff.core.keywords import GRAPH, RESPONSE, TRANSITIONS
from dff.core import Context, Actor
import dff.conditions as cnd

import dff_node_stats

stats_file = pathlib.Path("examples/stats.csv")
if stats_file.exists():
    stats_file.unlink()

transitions = {
    "root": {
        "start": [
            "hi",
            "i like animals",
            "let's talk about animals",
        ]
    },
    "animals": {
        "have_pets": ["yes"],
        "like_animals": ["yes"],
        "what_animal": ["bird", "dog"],
        "ask_about_breed": ["pereat", "bulldog", "i do not known"],
    },
}
# a dialog script
flows = {
    "root": {
        GRAPH: {
            "start": {
                RESPONSE: "Hi",
                TRANSITIONS: {
                    ("animals", "ask_some_questions"): cnd.exact_match("hi"),
                    ("animals", "have_pets"): cnd.exact_match("i like animals"),
                    ("animals", "like_animals"): cnd.exact_match("let's talk about animals"),
                },
            },
            "fallback": {RESPONSE: "Oops"},
        },
    },
    "animals": {
        GRAPH: {
            "ask_some_questions": {RESPONSE: "how are you"},
            "have_pets": {RESPONSE: "do you have pets?", TRANSITIONS: {"what_animal": cnd.exact_match("yes")}},
            "like_animals": {RESPONSE: "do you like it?", TRANSITIONS: {"what_animal": cnd.exact_match("yes")}},
            "what_animal": {
                RESPONSE: "what animals do you have?",
                TRANSITIONS: {
                    "ask_about_color": cnd.exact_match("bird"),
                    "ask_about_breed": cnd.exact_match("dog"),
                },
            },
            "ask_about_color": {RESPONSE: "what color is it"},
            "ask_about_breed": {
                RESPONSE: "what is this breed?",
                TRANSITIONS: {
                    "ask_about_breed": cnd.exact_match("pereat"),
                    "tell_fact_about_breed": cnd.exact_match("bulldog"),
                    "ask_about_training": cnd.exact_match("i do not known"),
                },
            },
            "tell_fact_about_breed": {
                RESPONSE: "Bulldogs appeared in England as specialized bull-baiting dogs. ",
            },
            "ask_about_training": {RESPONSE: "Do you train your dog? "},
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
        flow, node = ctx.node_labels.get(ctx.previous_index, ["root", "fallback"])
        if [flow, node] == ["root", "fallback"]:
            ctx = Context()
            flow, node = ["root", "start"]
        answers = list(transitions.get(flow, {}).get(node, []))
        in_text = random.choice(answers) if answers else "go to fallback"
        ctx.add_request(in_text)
        ctx = actor(ctx)
        ctx.clear(hold_last_n_indexes=3)
        ctxs[j] = ctx
    if i % 50 == 0:
        stats.save()
