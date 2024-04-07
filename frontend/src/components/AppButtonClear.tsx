import { useState } from "react";
import { ClearableSection } from "@/types/status";
import "./AppButtonClear.scss";

type ButtonClearProps = {
  target: ClearableSection;
  updateStatus: () => Promise<void>;
};

export const AppButtonClear = (props: ButtonClearProps) => {
  const { target, updateStatus } = props;
  const [isFetching, setIsFetching] = useState(false);

  /**
   * クリア処理
   * @param key 対象セクションキー
   */
  const handleClear: (key: ClearableSection) => Promise<void> = async (key) => {
    setIsFetching(true);
    await clear(key);
    await updateStatus();
    setIsFetching(false);
  };

  /**
   * クリア(単体処理)
   * @param key 対象セクションキー
   */
  const clear: (key: ClearableSection) => Promise<void> = async (key) => {
    const url = new URL(`/api/clear_${key}`, import.meta.env.VITE_SERVER);
    try {
      const response = await fetch(url, {
        method: "POST",
      });
      const json = await response.json();
      console.info(key, json.message);
    } catch (error) {
      console.error(error);
      return;
    }
  };

  return (
    <button
      disabled={isFetching}
      className="clear-button"
      onClick={() => handleClear(target)}
    >
      <span>{`clear ${target}`}</span>
      {isFetching && (
        <div className="loading-wrapper">
          <div className="loading" />
        </div>
      )}
    </button>
  );
};
