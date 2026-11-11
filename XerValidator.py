
import pandas as pd


def validate_xer(xer_data, high_float_threshold=80.0):
    """Find missing links, negative float, and high float."""

    task_df = xer_data.get_table("TASK").copy()
    taskpred_df = xer_data.get_table("TASKPRED").copy()

    if task_df.empty:
        raise ValueError("The XER file has no activities.")

    required_task_columns = {
        "task_id",
        "total_float_hr_cnt"
    }

    if not required_task_columns.issubset(task_df.columns):
        raise ValueError("TASK table is missing required columns.")

    if not {"task_id", "pred_task_id"}.issubset(taskpred_df.columns):
        taskpred_df = pd.DataFrame(
            columns=["task_id", "pred_task_id"]
        )

    # Normalize IDs.
    task_df["task_id"] = (
        task_df["task_id"].astype("string").str.strip()
    )

    taskpred_df["task_id"] = (
        taskpred_df["task_id"].astype("string").str.strip()
    )

    taskpred_df["pred_task_id"] = (
        taskpred_df["pred_task_id"].astype("string").str.strip()
    )

    # Keep activities with valid IDs.
    valid_tasks = task_df[
        task_df["task_id"].notna()
        & (task_df["task_id"] != "")
    ].copy()

    task_ids = set(valid_tasks["task_id"])

    # Keep relationships referencing existing activities.
    valid_relationships = taskpred_df[
        taskpred_df["task_id"].notna()
        & taskpred_df["pred_task_id"].notna()
        & (taskpred_df["task_id"] != "")
        & (taskpred_df["pred_task_id"] != "")
    ].copy()

    valid_relationships = valid_relationships[
        valid_relationships["task_id"].isin(task_ids)
        & valid_relationships["pred_task_id"].isin(task_ids)
    ]

    # Identify activities with predecessors and successors.
    activities_with_predecessors = set(
        valid_relationships["task_id"]
    )

    activities_with_successors = set(
        valid_relationships["pred_task_id"]
    )

    # Milestones are allowed to sit at the edge of the network:
    #   TT_Mile    = start milestone  -> no predecessor expected
    #   TT_FinMile = finish milestone -> no successor expected
    task_type = valid_tasks.get(
        "task_type", pd.Series("", index=valid_tasks.index)
    ).astype("string").str.strip()

    no_predecessor = (
        ~valid_tasks["task_id"].isin(activities_with_predecessors)
        & (task_type != "TT_Mile")
    )

    no_successor = (
        ~valid_tasks["task_id"].isin(activities_with_successors)
        & (task_type != "TT_FinMile")
    )

    # One row per activity, labelled with what is missing.
    missing_links = valid_tasks[no_predecessor | no_successor].copy()

    missing_links["missing_type"] = "Successor"
    missing_links.loc[
        no_predecessor[missing_links.index]
        & ~no_successor[missing_links.index],
        "missing_type"
    ] = "Predecessor"
    missing_links.loc[
        no_predecessor[missing_links.index]
        & no_successor[missing_links.index],
        "missing_type"
    ] = "Predecessor and Successor"

    missing_links = missing_links.reset_index(drop=True)

    # Convert total float into numeric values.
    valid_tasks["total_float_hr_cnt"] = pd.to_numeric(
        valid_tasks["total_float_hr_cnt"],
        errors="coerce"
    )

    # Find negative float.
    negative_float = valid_tasks[
        valid_tasks["total_float_hr_cnt"] < 0
    ].copy()

    # Find high float.
    high_float = valid_tasks[
        valid_tasks["total_float_hr_cnt"] > high_float_threshold
    ].copy()

    return {
        "missing_links": missing_links,
        "negative_float": negative_float,
        "high_float": high_float
    }
