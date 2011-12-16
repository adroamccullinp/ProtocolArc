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
