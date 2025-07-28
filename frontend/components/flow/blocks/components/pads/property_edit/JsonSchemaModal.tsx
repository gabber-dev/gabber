/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import React, { useMemo, useState } from "react";

type Props = {
  title: string;
  schema: Record<string, any>;
  setSchema: (schema: Record<string, any>) => void;
};

export function JsonSchemaModal({ title, schema, setSchema }: Props) {
  const typeOptions = ["string", "number", "boolean"];

  const propCount = useMemo(() => {
    return Object.keys(schema.properties || {}).length || 0;
  }, [schema.properties]);

  const properties: Record<string, any> = useMemo(() => {
    return schema.properties || {};
  }, [schema.properties]);

  const required = useMemo(() => {
    return schema.required || [];
  }, [schema.required]);

  // Convert properties object to an array of [name, value] pairs
  const propertyEntries = useMemo(() => {
    return Object.entries(properties);
  }, [properties]);

  const addProperty = (): void => {
    const defaultPropName = `property${propCount}`;
    setSchema({
      ...schema,
      properties: {
        ...schema.properties,
        [defaultPropName]: { type: "string" },
      },
      required: [...(schema.required || []), defaultPropName],
    });
  };

  const updateProperty = (
    propName: string,
    updates: Record<string, any>,
  ): void => {
    setSchema({
      ...schema,
      properties: {
        ...schema.properties,
        [propName]: {
          ...schema.properties[propName],
          ...updates,
        },
      },
      required: schema.required?.includes(propName)
        ? schema.required.map((name: string) =>
            name === propName
              ? { ...schema.properties[propName], ...updates }
              : name,
          )
        : schema.required || [],
    });
  };

  const renameProperty = (oldName: string, newName: string): void => {
    if (newName && newName !== oldName && !schema.properties[newName]) {
      const newProperties = { ...schema.properties };
      newProperties[newName] = newProperties[oldName];
      delete newProperties[oldName];
      setSchema({
        ...schema,
        properties: newProperties,
        required: schema.required?.includes(oldName)
          ? schema.required.map((name: string) =>
              name === oldName ? newName : name,
            )
          : schema.required || [],
      });
    }
  };

  const toggleRequired = (propName: string): void => {
    setSchema({
      ...schema,
      required: schema.required?.includes(propName)
        ? schema.required.filter((name: string) => name !== propName)
        : [...(schema.required || []), propName],
    });
  };

  const deleteProperty = (propName: string): void => {
    const newProperties = { ...schema.properties };
    delete newProperties[propName];
    setSchema({
      ...schema,
      properties: newProperties,
      required:
        schema.required?.filter((name: string) => name !== propName) || [],
    });
  };

  return (
    <div className="flex flex-col items-center">
      <div className="flex gap-1">
        <h1 className="text-lg font-bold">{title}</h1>
        <button className="btn btn-primary btn-sm" onClick={addProperty}>
          Add Property
        </button>
      </div>

      <div className="space-y-2">
        {propertyEntries.map(([name, prop]: [string, any], index: number) => (
          <div key={index} className="card bg-base-100 shadow-md p-2">
            <div className="flex justify-between items-center mb-1">
              <input
                type="text"
                className="input input-bordered input-sm text-base font-semibold"
                value={name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  renameProperty(name, e.target.value)
                }
                placeholder="Property name"
              />
              <button
                className="btn btn-error btn-xs ml-2"
                onClick={() => deleteProperty(name)}
              >
                Delete
              </button>
            </div>

            <div className="form-control">
              <label className="label py-1">
                <span className="label-text text-sm">Type</span>
              </label>
              <select
                className="select select-bordered select-sm"
                value={prop.type || "string"}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  updateProperty(name, {
                    type: e.target.value,
                  })
                }
              >
                {typeOptions.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-control">
              <label className="label cursor-pointer py-1">
                <span className="label-text text-sm">Required</span>
                <input
                  type="checkbox"
                  className="toggle toggle-sm"
                  checked={schema.required?.includes(name) || false}
                  onChange={() => toggleRequired(name)}
                />
              </label>
            </div>

            <div className="form-control">
              <label className="label py-1">
                <span className="label-text text-sm">Default Value</span>
              </label>
              <input
                type="text"
                className="input input-bordered input-sm"
                value={prop.default || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  updateProperty(name, { default: e.target.value })
                }
                placeholder="Default value"
              />
            </div>

            {["number"].includes(prop.type) && (
              <div className="grid grid-cols-2 gap-2">
                <div className="form-control">
                  <label className="label py-1">
                    <span className="label-text text-sm">Minimum</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered input-sm"
                    value={prop.minimum ?? ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateProperty(name, {
                        minimum: e.target.value
                          ? Number(e.target.value)
                          : undefined,
                      })
                    }
                    placeholder="Min"
                  />
                </div>
                <div className="form-control">
                  <label className="label py-1">
                    <span className="label-text text-sm">Maximum</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered input-sm"
                    value={prop.maximum ?? ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateProperty(name, {
                        maximum: e.target.value
                          ? Number(e.target.value)
                          : undefined,
                      })
                    }
                    placeholder="Max"
                  />
                </div>
              </div>
            )}

            {prop.type === "string" && (
              <div className="grid grid-cols-2 gap-2">
                <div className="form-control">
                  <label className="label py-1">
                    <span className="label-text text-sm">Min Length</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered input-sm"
                    value={prop.minLength ?? ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateProperty(name, {
                        minLength: e.target.value
                          ? Number(e.target.value)
                          : undefined,
                      })
                    }
                    placeholder="Min len"
                  />
                </div>
                <div className="form-control">
                  <label className="label py-1">
                    <span className="label-text text-sm">Max Length</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered input-sm"
                    value={prop.maxLength ?? ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateProperty(name, {
                        maxLength: e.target.value
                          ? Number(e.target.value)
                          : undefined,
                      })
                    }
                    placeholder="Max len"
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
