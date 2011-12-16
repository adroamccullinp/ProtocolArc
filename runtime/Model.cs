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

