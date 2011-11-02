using System.Text.Json;

namespace ProtocolArc.Runtime;

/// <summary>
/// Parses contract and envelope documents from JSON using only
/// <c>System.Text.Json</c>. Malformed documents raise
/// <see cref="ContractException"/> with a precise message.
/// </summary>
public static class Loader
{
    public static Contract ParseContract(JsonElement doc, string source)
    {
        if (doc.ValueKind != JsonValueKind.Object)
            throw new ContractException($"{source}: contract must be a JSON object");

        var name = RequireString(doc, "name", source);
        var revision = RequireString(doc, "revision", source);

        var fields = new List<FieldSpec>();
        var seen = new HashSet<string>();
        if (doc.TryGetProperty("fields", out var fieldsEl) && fieldsEl.ValueKind == JsonValueKind.Array)
        {
            int idx = 0;
            foreach (var f in fieldsEl.EnumerateArray())
            {
                var where = $"{source}: fields[{idx}]";
                if (f.ValueKind != JsonValueKind.Object)
                    throw new ContractException($"{where}: each field must be an object");
                var fname = RequireString(f, "name", where);
                if (!seen.Add(fname))
                    throw new ContractException($"{where}: duplicate field name '{fname}'");

                var types = ReadTypes(f, where);
                List<JsonElement>? enumValues = null;
                if (f.TryGetProperty("enum", out var enumEl) && enumEl.ValueKind == JsonValueKind.Array)
                    enumValues = enumEl.EnumerateArray().Select(e => e.Clone()).ToList();

                bool required = !f.TryGetProperty("required", out var reqEl) ||
                                reqEl.ValueKind != JsonValueKind.False;

                string docText = f.TryGetProperty("doc", out var docEl) &&
                                 docEl.ValueKind == JsonValueKind.String
                    ? docEl.GetString() ?? ""
                    : "";

                fields.Add(new FieldSpec(fname, types, required, enumValues, docText));
                idx++;
            }
        }

        return new Contract
        {
            Name = name,
            Revision = revision,
            Kind = ReadString(doc, "kind", "generic"),
            Title = ReadString(doc, "title", name),
            Strict = doc.TryGetProperty("strict", out var s) && s.ValueKind == JsonValueKind.True,
            Fields = fields
        };
    }

    public static Envelope ParseEnvelope(JsonElement doc, string source)
    {
        if (doc.ValueKind != JsonValueKind.Object)
            throw new ContractException($"{source}: envelope must be a JSON object");

        var contract = RequireString(doc, "contract", source);
        string? revision = doc.TryGetProperty("revision", out var revEl) &&
                           revEl.ValueKind == JsonValueKind.String
            ? revEl.GetString()
            : null;

