import json
import pickle
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "ml" / "models" / "occupancy_model.pkl"
OUTPUT_PATH = ROOT / "ml" / "models" / "occupancy_model.json"


def export_tree(tree):
    structure = tree.tree_

    return {
        "children_left": structure.children_left.tolist(),
        "children_right": structure.children_right.tolist(),
        "feature": structure.feature.tolist(),
        "threshold": structure.threshold.tolist(),
        "value": structure.value[:, 0, 0].tolist()
    }


def main():

    with MODEL_PATH.open("rb") as f:
        bundle = pickle.load(f)

    model = bundle["model"]

    exported = {
        "features": bundle["features"],
        "n_estimators": len(model.estimators_),
        "trees": [
            export_tree(tree)
            for tree in model.estimators_
        ]
    }

    OUTPUT_PATH.write_text(
        json.dumps(exported),
        encoding="utf-8"
    )

    print("Modelo exportado correctamente")
    print(f"Arboles: {len(model.estimators_)}")
    print(f"Archivo: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()