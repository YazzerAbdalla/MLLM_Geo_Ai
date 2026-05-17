import pandas as pd

def verify_dataset(csv_path: str):
    df = pd.read_csv(csv_path)

    print("\nDATASET SUMMARY")
    print("----------------------")

    # 1 Number of rows
    print("Number of rows:", len(df))

    # 2 Class distribution
    print("\nLabel distribution:")
    print(df["label"].value_counts())

    # 3 Missing values
    print("\nMissing values per column:")
    print(df.isnull().sum())


if __name__ == "__main__":
    csv_path = r"C:\Users\YOUSIF\Desktop\MLLM_Geo_Ai-fresh-start\MLLM_Geo_Ai-fresh-start\data\raw\project.csv"
    verify_dataset(csv_path)