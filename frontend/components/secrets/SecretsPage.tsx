/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { useRepository } from "@/hooks/useRepository";
import { useState } from "react";
import {
  PlusIcon,
  KeyIcon,
  PencilIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

interface SecretsPageProps {
  storageDescription?: string | null;
}

export function SecretsPage({ storageDescription }: SecretsPageProps = {}) {
  const {
    secrets,
    secretsLoading,
    refreshSecrets,
    addSecret,
    updateSecret,
    deleteSecret,
  } = useRepository();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSecretName, setNewSecretName] = useState("");
  const [newSecretValue, setNewSecretValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingSecret, setEditingSecret] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [editValue, setEditValue] = useState("");

  const handleDeleteSecret = async (secretId: string, secretName: string) => {
    if (
      window.confirm(
        `Are you sure you want to delete the secret "${secretName}"? This action cannot be undone.`,
      )
    ) {
      setIsSubmitting(true);
      try {
        await deleteSecret(secretId);
      } catch (error) {
        console.error("Failed to delete secret:", error);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const handleAddSecret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSecretName.trim() || !newSecretValue.trim()) return;

    setIsSubmitting(true);
    try {
      await addSecret(newSecretName.trim(), newSecretValue);
      setNewSecretName("");
      setNewSecretValue("");
      setShowAddForm(false);
    } catch (error) {
      console.error("Failed to add secret:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateSecret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSecret || !editValue.trim()) return;

    setIsSubmitting(true);
    try {
      await updateSecret(editingSecret.id, editingSecret.name, editValue);
      setEditingSecret(null);
      setEditValue("");
    } catch (error) {
      console.error("Failed to update secret:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const startEditing = (secretId: string, secretName: string) => {
    setEditingSecret({ id: secretId, name: secretName });
    setEditValue("");
    setShowAddForm(false); // Close add form if open
  };

  const cancelEditing = () => {
    setEditingSecret(null);
    setEditValue("");
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <KeyIcon className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold text-base-content">
            Secrets Management
          </h1>
        </div>
        <button
          onClick={() => {
            setShowAddForm(true);
            setEditingSecret(null); // Close edit if open
          }}
          className="btn btn-primary gap-2"
          disabled={showAddForm || editingSecret !== null}
        >
          <PlusIcon className="w-5 h-5" />
          Add Secret
        </button>
      </div>

      {showAddForm && (
        <div className="card bg-base-200 shadow-lg mb-6">
          <div className="card-body">
            <h2 className="card-title text-lg mb-4">Add New Secret</h2>
            <form onSubmit={handleAddSecret} className="space-y-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">Secret Name</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., OPENAI_API_KEY"
                  className="input input-bordered w-full"
                  value={newSecretName}
                  onChange={(e) => setNewSecretName(e.target.value)}
                  required
                />
              </div>
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">Secret Value</span>
                </label>
                <input
                  type="password"
                  placeholder="Enter secret value"
                  className="input input-bordered w-full"
                  value={newSecretValue}
                  onChange={(e) => setNewSecretValue(e.target.value)}
                  required
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setNewSecretName("");
                    setNewSecretValue("");
                  }}
                  className="btn btn-ghost"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <span className="loading loading-spinner loading-sm"></span>
                  ) : (
                    "Add Secret"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingSecret && (
        <div className="card bg-base-200 shadow-lg mb-6">
          <div className="card-body">
            <h2 className="card-title text-lg mb-4">
              Update Secret: {editingSecret.name}
            </h2>
            <form onSubmit={handleUpdateSecret} className="space-y-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">
                    New Secret Value
                  </span>
                </label>
                <input
                  type="password"
                  placeholder="Enter new secret value"
                  className="input input-bordered w-full"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  required
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={cancelEditing}
                  className="btn btn-ghost"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <span className="loading loading-spinner loading-sm"></span>
                  ) : (
                    "Update Secret"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card bg-base-100 shadow-lg">
        <div className="card-body">
          <div className="flex items-center justify-between mb-4">
            <h2 className="card-title">Available Secrets</h2>
            <button
              onClick={refreshSecrets}
              className="btn btn-ghost btn-sm"
              disabled={secretsLoading}
            >
              {secretsLoading ? (
                <span className="loading loading-spinner loading-sm"></span>
              ) : (
                "Refresh"
              )}
            </button>
          </div>

          {secretsLoading ? (
            <div className="flex justify-center items-center py-8">
              <span className="loading loading-spinner loading-lg"></span>
            </div>
          ) : secrets.length === 0 ? (
            <div className="text-center py-8">
              <KeyIcon className="w-16 h-16 text-base-300 mx-auto mb-4" />
              <p className="text-base-content/60 text-lg">
                No secrets configured
              </p>
              <p className="text-base-content/40 text-sm">
                Add your first secret to get started
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="table w-full">
                <thead>
                  <tr>
                    <th>Secret Name</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {secrets.map((secret) => (
                    <tr key={secret.id} className="hover">
                      <td>
                        <div className="flex items-center gap-2">
                          <KeyIcon className="w-4 h-4 text-primary" />
                          <span className="font-medium">{secret.name}</span>
                        </div>
                      </td>
                      <td className="text-right">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => startEditing(secret.id, secret.name)}
                            className="btn btn-ghost btn-sm gap-1"
                            disabled={
                              editingSecret !== null ||
                              showAddForm ||
                              isSubmitting
                            }
                            title="Edit secret value"
                          >
                            <PencilIcon className="w-4 h-4" />
                            Edit
                          </button>
                          <button
                            onClick={() =>
                              handleDeleteSecret(secret.id, secret.name)
                            }
                            className="btn btn-ghost btn-sm gap-1 text-error hover:bg-error hover:text-error-content"
                            disabled={
                              editingSecret !== null ||
                              showAddForm ||
                              isSubmitting
                            }
                            title="Delete secret"
                          >
                            <TrashIcon className="w-4 h-4" />
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {storageDescription !== null && (
        <div className="mt-6 text-sm text-base-content/60">
          <p>
            <strong>Note:</strong>{" "}
            {storageDescription ||
              "Secrets are stored in your configured .secret file. Make sure to keep this file secure and never commit it to version control."}
          </p>
        </div>
      )}
    </div>
  );
}
