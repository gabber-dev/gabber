/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

export const checkSnakeCase = (name: string) => {
  if (name.toLowerCase() !== name) {
    return false;
  }

  const pat = /^[a-z]+(?:_[a-z]+)*$/;
  return pat.test(name);
};
