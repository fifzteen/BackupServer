// 各バックアップタスク
export type Task = {
  name: string;
  updated_at: string;
};

// セクション名
export type ClearableSection = "error" | "finished";
export type Section = ClearableSection | "running" | "pending";

// バックアップステータス全体のオブジェクト
export type Status = {
  [key in Section]: Task[];
};
