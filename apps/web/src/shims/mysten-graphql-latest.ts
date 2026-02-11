export function graphql(
  strings: TemplateStringsArray,
  ...values: Array<string | number>
): string {
  let out = "";
  for (let i = 0; i < strings.length; i += 1) {
    out += strings[i];
    if (i < values.length) {
      out += String(values[i]);
    }
  }
  return out;
}
