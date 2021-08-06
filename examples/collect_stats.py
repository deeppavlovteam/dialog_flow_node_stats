from dff import GRAPH, RESPONSE, GLOBAL_TRANSITIONS
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
        GLOBAL_TRANSITIONS: {**create_transitions()},
        GRAPH: {
            "start": {RESPONSE: "s"},
            "fallback": {RESPONSE: "f"},
        },
    },
    "left": {
        GRAPH: {
            "step_0": {RESPONSE: "l0"},
            "step_1": {RESPONSE: "l1"},
            "step_2": {RESPONSE: "l2"},
            "step_3": {RESPONSE: "l3"},
            "step_4": {RESPONSE: "l4"},
        },
    },
    "right": {
        GRAPH: {
            "step_0": {RESPONSE: "r0"},
            "step_1": {RESPONSE: "r1"},
            "step_2": {RESPONSE: "r2"},
            "step_3": {RESPONSE: "r3"},
            "step_4": {RESPONSE: "r4"},
        },
    },
}

ctx1 = Context()
ctx2 = Context()
actor = Actor(flows, start_node_label=("root", "start"), fallback_node_label=("root", "fallback"))
stats = dff_node_stats.Stats(csv_file="examples/stat.csv")
for in_text, out_text in [
    ("start", "s"),
    ("left", "l2"),
    ("left", "l2"),
    ("123", "l2"),
    ("asd", "l2"),
    ("right", "r2"),
    ("fallback", "f"),
    ("left", "l2"),
    ("forward", "l3"),
    ("forward", "l4"),
    ("forward", "f"),
    ("right", "r2"),
    ("back", "r1"),
    ("back", "r0"),
    ("back", "f"),
    ("start", "s"),
]:
    ctx1.add_human_utterance(in_text)
    ctx2.add_human_utterance(in_text)
    ctx1 = actor(ctx1)
    ctx1.clean(hold_last_n_indexes=4, field_names=["labels"])
    stats.save(ctx1)
    ctx2 = actor(ctx2)
    ctx2.clean(hold_last_n_indexes=4, field_names=["labels"])
    stats.save(ctx2)
