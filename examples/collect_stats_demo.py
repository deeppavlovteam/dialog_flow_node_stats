import random


from dff import GRAPH, RESPONSE, TRANSITIONS
from dff import Context, Actor
from dff import repeat, previous, to_start, to_fallback, forward, back

# from dff_node_stats import Stats
import dff_node_stats


def always_true(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return True


def create_transitions():
    return {
        ("left", "step_2"): "left",
        ("right", "step_2"): "right",
        previous(): "previous",
        to_start(): "start",
        to_fallback(): "fallback",
        forward(): "forward",
        back(): "back",
        previous(): "previous",
        repeat(): always_true,
    }


# a dialog script
flows = {
    "root": {
        GRAPH: {
            "start": {RESPONSE: "f", TRANSITIONS: {"ask_some_questions": "1", "have_pets": "2", "like_animals": "3"}},
            "ask_some_questions": {RESPONSE: "f", TRANSITIONS: {}},
            "have_pets": {RESPONSE: "f", TRANSITIONS: {"what_animal": "1"}},
            "like_animals": {RESPONSE: "f", TRANSITIONS: {"what_animal": "1"}},
            "what_animal": {RESPONSE: "f", TRANSITIONS: {"ask_about_color": "1", "ask_about_breed": "2"}},
            "ask_about_color": {RESPONSE: "f", TRANSITIONS: {}},
            "ask_about_breed": {
                RESPONSE: "f",
                TRANSITIONS: {"ask_about_breed": "1", "tell_fact_about_breed": "2", "ask_about_training": "3"},
            },
            "tell_fact_about_breed": {RESPONSE: "f", TRANSITIONS: {}},
            "ask_about_training": {RESPONSE: "f", TRANSITIONS: {}},
        },
    },
}

ctx1 = Context()
ctx2 = Context()
actor = Actor(flows, start_node_label=("root", "start"))
stats = dff_node_stats.Stats(csv_file="examples/stat.csv")
for _ in range(1000):
    node = ctx1.node_label_history.get(ctx1.previous_history_index, ["root", "start"])[1]
    answers = list(flows["root"][GRAPH][node][TRANSITIONS].values())
    in_text = random.choice(answers) if answers else "123"
    ctx1.add_human_utterance(in_text)
    ctx1 = actor(ctx1)
    ctx1.clean(hold_last_n_indexes=4, field_names=["labels"])
    stats.save(ctx1)
