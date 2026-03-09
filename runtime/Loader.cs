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

        JsonElement data;
        if (doc.TryGetProperty("data", out var dataEl) && dataEl.ValueKind == JsonValueKind.Object)
        {
            data = dataEl.Clone();
        }
        else
        {
            // Bare form: build an object without the routing keys.
            using var stream = new MemoryStream();
            using (var writer = new Utf8JsonWriter(stream))
            {
                writer.WriteStartObject();
                foreach (var prop in doc.EnumerateObject())
                {
                    if (prop.Name is "contract" or "revision") continue;
                    prop.WriteTo(writer);
                }
                writer.WriteEndObject();
            }
            stream.Position = 0;
            using var parsed = JsonDocument.Parse(stream);
            data = parsed.RootElement.Clone();
        }

        return new Envelope
        {
            Contract = contract,
            Revision = revision,
            Data = data,
            Source = source
        };
    }

    private static IReadOnlyList<string> ReadTypes(JsonElement f, string where)
    {
        if (!f.TryGetProperty("type", out var typeEl))
            throw new ContractException($"{where}: missing required key 'type'");

        var types = new List<string>();
        if (typeEl.ValueKind == JsonValueKind.String)
        {
            types.Add(typeEl.GetString()!);
        }
        else if (typeEl.ValueKind == JsonValueKind.Array)
        {
            foreach (var t in typeEl.EnumerateArray())
                types.Add(t.GetString() ?? "");
        }
        else
        {
            throw new ContractException($"{where}: 'type' must be a string or list");
        }

        foreach (var t in types)
            if (!JsonTypes.All.Contains(t))
                throw new ContractException($"{where}: unknown type '{t}'");

        if (types.Count == 0)
            throw new ContractException($"{where}: 'type' must be non-empty");
        return types;
    }

    private static string RequireString(JsonElement doc, string key, string where)
    {
        if (!doc.TryGetProperty(key, out var el))
            throw new ContractException($"{where}: missing required key '{key}'");
        return el.ValueKind == JsonValueKind.String ? el.GetString()! : el.ToString();
    }

    private static string ReadString(JsonElement doc, string key, string fallback)
    {
        return doc.TryGetProperty(key, out var el) && el.ValueKind == JsonValueKind.String
            ? el.GetString() ?? fallback
            : fallback;
    }
}

/// <summary>Raised when a document cannot be understood at all.</summary>
public sealed class ContractException : Exception
{
    public ContractException(string message) : base(message) { }
}

# draft note 52
