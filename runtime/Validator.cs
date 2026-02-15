using System.Text.Json;

namespace ProtocolArc.Runtime;

/// <summary>
/// Validates an <see cref="Envelope"/> against a <see cref="Contract"/>,
/// producing an ordered set of <see cref="Finding"/> records. The rule set and
/// severities match the Python package exactly.
/// </summary>
public static class Validator
{
    private static readonly Dictionary<string, int> SeverityRank = new()
    {
        ["info"] = 0,
        ["warning"] = 1,
        ["error"] = 2
    };

    public static List<Finding> Validate(Contract contract, Envelope envelope)
    {
        var findings = new List<Finding>();

        if (envelope.Contract != contract.Name)
        {
            findings.Add(new Finding(
                "contract.match", "<envelope>", "error",
                $"envelope targets '{envelope.Contract}' but validated against '{contract.Name}'"));
        }

        if (!string.IsNullOrEmpty(envelope.Revision) && envelope.Revision != contract.Revision)
        {
            findings.Add(new Finding(
                "revision.hint", "<envelope>", "warning",
                $"envelope declares revision '{envelope.Revision}', contract is '{contract.Revision}'"));
        }

        foreach (var spec in contract.Fields)
        {
            var (present, value) = ResolvePath(envelope.Data, spec.Name);
            if (!present)
            {
                if (spec.Required)
                    findings.Add(new Finding(
                        "field.required", spec.Name, "error",
                        $"required field '{spec.Name}' is missing"));
                continue;
            }

            var actual = JsonTypes.Of(value);
            if (!spec.AcceptsType(actual))
            {
                findings.Add(new Finding(
                    "field.type", spec.Name, "error",
                    $"field '{spec.Name}' has type '{actual}', expected '{spec.TypeLabel()}'"));
                continue;
            }

            if (spec.Enum is { Count: > 0 } && !EnumContains(spec.Enum, value))
            {
                findings.Add(new Finding(
                    "field.enum", spec.Name, "error",
                    $"field '{spec.Name}' value not in allowed set"));
            }
        }

        if (contract.Strict && envelope.Data.ValueKind == JsonValueKind.Object)
        {
            var roots = contract.Fields
                .Select(f => f.Name.Split('.')[0])
                .ToHashSet();
            foreach (var prop in envelope.Data.EnumerateObject().OrderBy(p => p.Name, StringComparer.Ordinal))
            {
                if (!roots.Contains(prop.Name))
                    findings.Add(new Finding(
                        "field.unknown", prop.Name, "warning",
                        $"field '{prop.Name}' is not declared by a strict contract"));
            }
        }

        return Order(findings);
    }

    public static List<Finding> Order(List<Finding> findings) =>
        findings
            .OrderByDescending(f => SeverityRank.GetValueOrDefault(f.Severity, 0))
            .ThenBy(f => f.Field, StringComparer.Ordinal)
            .ThenBy(f => f.Rule, StringComparer.Ordinal)
            .ToList();

    public static bool HasError(IEnumerable<Finding> findings) =>
        findings.Any(f => f.Severity == "error");

    private static (bool, JsonElement) ResolvePath(JsonElement data, string dotted)
    {
        var cursor = data;
        foreach (var segment in dotted.Split('.'))
        {
            if (cursor.ValueKind != JsonValueKind.Object ||
                !cursor.TryGetProperty(segment, out var next))
                return (false, default);
            cursor = next;
        }
        return (true, cursor);
    }

    private static bool EnumContains(IReadOnlyList<JsonElement> allowed, JsonElement value)
    {
        foreach (var candidate in allowed)
        {
            if (candidate.ValueKind != value.ValueKind) continue;
            if (candidate.GetRawText() == value.GetRawText()) return true;
        }
        return false;
    }
}

# draft note 40
