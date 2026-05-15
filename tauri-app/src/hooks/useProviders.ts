import { useState, useEffect, useCallback } from "react";
import { invoke } from "../lib/tauri";
import type { ConfigResponse, Preset, AddProviderInput, UpdateProviderInput } from "../types/provider";

export function useProviders() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [cfg, pre] = await Promise.all([
        invoke<ConfigResponse>("get_config"),
        invoke<Preset[]>("get_presets"),
      ]);
      setConfig(cfg);
      setPresets(pre);
      setError(null);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const addProvider = async (input: AddProviderInput) => {
    await invoke("add_provider", { input });
    await refresh();
  };

  const updateProvider = async (input: UpdateProviderInput) => {
    await invoke("update_provider", { input });
    await refresh();
  };

  const deleteProvider = async (id: string) => {
    await invoke("delete_provider", { id });
    await refresh();
  };

  const activateProvider = async (id: string) => {
    await invoke("activate_provider", { id });
    await refresh();
  };

  const testProvider = async (id: string): Promise<string> => {
    return invoke<string>("test_provider", { id });
  };

  return {
    config,
    presets,
    loading,
    error,
    refresh,
    addProvider,
    updateProvider,
    deleteProvider,
    activateProvider,
    testProvider,
  };
}
