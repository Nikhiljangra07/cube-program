"""run11_common.py — shared constants for RUN 11 (train-eval format alignment).

The revision instruction is IDENTICAL in the training rows and the Eval D
protocol — the trained trigger and the measured trigger are the same string.
"""
WRK_SYS = ("You write one precise, decisive, realistic reasoning thread pursuing a given "
           "strategic angle.")

REVISE_USER = ("PROBLEM: {problem}\n\nYOUR PREVIOUS PLAN: {prior}\n\nUPDATE: {update}\n\n"
               "The situation has changed as described in UPDATE. Revise your plan in 3-4 "
               "sentences, cold and analytical: (1) state precisely what the update changes "
               "for your plan, (2) give the revised plan — reallocate what freed up or "
               "absorb what tightened, concretely, (3) state how your success estimate "
               "responds and why — move it proportionately in the direction the update "
               "implies, or hold it only if the constraint it rests on did not move, and "
               "name that constraint. Final line, exactly: ESTIMATE: NN%")
