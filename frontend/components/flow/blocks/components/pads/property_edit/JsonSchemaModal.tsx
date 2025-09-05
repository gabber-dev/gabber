/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { XCircleIcon } from "@heroicons/react/24/outline";
import React, { useMemo } from "react";

type Props = {
  title: string;
  schema: Record<string, unknown>;
  setSchema: (schema: Record<string, unknown>) => void;
};

type PropertyEditorProps = {
  name: string;
  prop: any;
  renameProperty: (oldName: string, newName: string) => void;
  updateProperty: (propName: string, updates: Record<string, any>) => void;
  setDefault: (propName: string, defaultValue: any) => void;
  toggleRequired: (propName: string) => void;
  deleteProperty: (propName: string) => void;
  schema: Record<string, unknown>;
};

function PropertyEditor({
  name,
  prop,
  renameProperty,
  updateProperty,
  setDefault,
  toggleRequired,
  deleteProperty,
  schema,
}: PropertyEditorProps) {
  const typeOptions = ["string", "number", "boolean"];

  return (
    <div className="card bg-base-100 shadow-md border border-base-200 p-2">
      <div className="flex gap-2 mb-1 items-end">
        <div className="form-control flex-grow">
          <label className="label py-0.5">
            <span className="label-text text-sm">Name</span>
          </label>
          <input
            type="text"
            className="input input-bordered input-sm font-semibold"
            value={name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              renameProperty(name, e.target.value)
            }
            placeholder="Property name"
          />
        </div>
        <div className="form-control w-32">
          <label className="label py-0.5">
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
        <button
          className="absolute top-1 right-1 w-6 h-6 cursor-pointer text-error"
          onClick={() => deleteProperty(name)}
        >
          <XCircleIcon />
        </button>
      </div>

      <div className="flex gap-2 mb-1">
        <div className="form-control flex-grow">
          <label className="label py-0.5">
            <span className="label-text text-sm">Default Value</span>
          </label>
          <input
            type="text"
            className="input input-bordered input-sm"
            value={schema.defaults?.[name] || ""}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setDefault(name, e.target.value)
            }
            placeholder="Default value"
          />
        </div>
        <div className="form-control">
          <label className="label cursor-pointer py-0.5 space-x-1">
            <span className="label-text text-sm">Required</span>
            <input
              type="checkbox"
              className="toggle toggle-sm"
              checked={schema.required?.includes(name) || false}
              onChange={() => toggleRequired(name)}
            />
          </label>
        </div>
      </div>

      {["number"].includes(prop.type) && (
        <div className="grid grid-cols-2 gap-1">
          <div className="form-control">
            <label className="label py-0.5">
              <span className="label-text text-sm">Minimum</span>
            </label>
            <input
              type="number"
              className="input input-bordered input-sm"
              value={prop.minimum ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateProperty(name, {
                  minimum: e.target.value ? Number(e.target.value) : undefined,
                })
              }
              placeholder="Min"
            />
          </div>
          <div className="form-control">
            <label className="label py-0.5">
              <span className="label-text text-sm">Maximum</span>
            </label>
            <input
              type="number"
              className="input input-bordered input-sm"
              value={prop.maximum ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateProperty(name, {
                  maximum: e.target.value ? Number(e.target.value) : undefined,
                })
              }
              placeholder="Max"
            />
          </div>
        </div>
      )}

      {prop.type === "string" && (
        <div className="grid grid-cols-2 gap-1">
          <div className="form-control">
            <label className="label py-0.5">
              <span className="label-text text-sm">Min Length</span>
            </label>
            <input
              type="number"
              className="input input-bordered input-sm"
              value={prop.min_length ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateProperty(name, {
                  min_length: e.target.value
                    ? Number(e.target.value)
                    : undefined,
                })
              }
              placeholder="Min len"
            />
          </div>
          <div className="form-control">
            <label className="label py-0.5">
              <span className="label-text text-sm">Max Length</span>
            </label>
            <input
              type="number"
              className="input input-bordered input-sm"
              value={prop.max_length ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateProperty(name, {
                  max_length: e.target.value
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
  );
}

export function JsonSchemaModal({ title, schema, setSchema }: Props) {
  const propCount = useMemo(() => {
    return Object.keys(schema.properties || {}).length || 0;
  }, [schema.properties]);

  const properties: Record<string, unknown> = useMemo(() => {
    return schema.properties || {};
  }, [schema.properties]);

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
          ...(schema.properties?.[propName] as object),
          ...updates,
        },
      },
    });
  };

  const setDefault = (propName: string, defaultValue: any): void => {
    setSchema({
      ...schema,
      defaults: {
        ...(schema.defaults || {}),
        [propName]: defaultValue,
      },
    });
  };

  const renameProperty = (oldName: string, newName: string): void => {
    if (newName && newName !== oldName && !schema.properties?.[newName]) {
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
      defaults: Object.fromEntries(
        Object.entries(schema.defaults || {}).filter(
          ([key]) => key !== propName,
        ),
      ),
    });
  };

  return (
    <div className="flex flex-col gap-4 max-w-md mx-auto p-4">
      <div className="flex justify-between items-center">
        <h1 className="text-lg font-bold">{title}</h1>
        <button className="btn btn-primary btn-sm" onClick={addProperty}>
          Add Property
        </button>
      </div>

      <div className="flex flex-col gap-2 max-h-[60vh] overflow-y-auto">
        {propertyEntries.map(([name, prop]: [string, any], index: number) => (
          <PropertyEditor
            key={index}
            name={name}
            prop={prop}
            renameProperty={renameProperty}
            updateProperty={updateProperty}
            setDefault={setDefault}
            toggleRequired={toggleRequired}
            deleteProperty={deleteProperty}
            schema={schema}
          />
        ))}
      </div>
    </div>
  );
}
