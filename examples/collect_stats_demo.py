import uuid
import random

import tqdm

from dff import GRAPH, RESPONSE, TRANSITIONS
from dff import Context, Actor

import dff_node_stats


# a dialog script
flows = {
    "root": {
        GRAPH: {
            "start": {
                RESPONSE: "Hi",
                TRANSITIONS: {
                    ("animals", "ask_some_questions"): "hi",
                    ("animals", "have_pets"): "i like animals",
                    ("animals", "like_animals"): "let's talk about animals",
                },
            },
            "fallback": {RESPONSE: "Oops"},
        },
    },
    "animals": {
        GRAPH: {
            "ask_some_questions": {RESPONSE: "how are you"},
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
}

actor = Actor(flows, start_node_label=("root", "start"), fallback_node_label=("root", "fallback"))
stats = dff_node_stats.Stats(hdf_file="examples/stat.h5")
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
