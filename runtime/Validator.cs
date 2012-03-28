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
