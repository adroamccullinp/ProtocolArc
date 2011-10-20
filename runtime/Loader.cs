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
