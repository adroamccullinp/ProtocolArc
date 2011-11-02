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

