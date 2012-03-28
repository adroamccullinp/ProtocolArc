using System.Text.Json;

namespace ProtocolArc.Runtime;

/// <summary>
/// Validates an <see cref="Envelope"/> against a <see cref="Contract"/>,
/// producing an ordered set of <see cref="Finding"/> records. The rule set and
/// severities match the Python package exactly.
/// </summary>
public static class Validator
{
