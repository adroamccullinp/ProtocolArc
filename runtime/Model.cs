using System.Text.Json;

namespace ProtocolArc.Runtime;

/// <summary>
/// JSON type names recognised by the ProtocolArc runtime. These mirror the
/// Python package so that a contract validated in either component yields the
/// same findings.
/// </summary>
public static class JsonTypes
{
    public static readonly string[] All =
    {
        "string", "integer", "number", "boolean", "object", "array", "null", "any"
    };

    /// <summary>Return the ProtocolArc type name for a JSON element.</summary>
    public static string Of(JsonElement element) => element.ValueKind switch
    {
        JsonValueKind.String => "string",
        JsonValueKind.True => "boolean",
        JsonValueKind.False => "boolean",
        JsonValueKind.Object => "object",
        JsonValueKind.Array => "array",
        JsonValueKind.Null => "null",
        JsonValueKind.Number => element.TryGetInt64(out _) ? "integer" : "number",
        _ => "any"
    };
}

/// <summary>Specification for a single contract field.</summary>
public sealed record FieldSpec(
    string Name,
    IReadOnlyList<string> Types,
    bool Required,
    IReadOnlyList<JsonElement>? Enum,
    string Doc)
{
    public bool AcceptsType(string typeName) =>
        Types.Contains("any") || Types.Contains(typeName);

    public string TypeLabel() => string.Join("|", Types);
}

/// <summary>A versioned protocol contract.</summary>
public sealed class Contract
{
    public required string Name { get; init; }
    public required string Revision { get; init; }
    public string Kind { get; init; } = "generic";
    public string Title { get; init; } = "";
    public bool Strict { get; init; }
    public List<FieldSpec> Fields { get; init; } = new();

    public string Identity() => $"{Name}@{Revision}";
}

/// <summary>A concrete protocol message instance.</summary>
public sealed class Envelope
{
    public required string Contract { get; init; }
    public string? Revision { get; init; }
    public required JsonElement Data { get; init; }
    public string Source { get; init; } = "<inline>";
}

/// <summary>A single validation observation.</summary>
public sealed record Finding(string Rule, string Field, string Severity, string Message);
