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
