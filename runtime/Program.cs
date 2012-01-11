using System.Text.Json;
using ProtocolArc.Runtime;

// ProtocolArc.Runtime — a native envelope validator.
//
// Usage:
//   ProtocolArc.Runtime validate <contract.json> <envelope.json|.jsonl> [--json]
//   ProtocolArc.Runtime describe <contract.json>
//   ProtocolArc.Runtime selfcheck
//
// The runtime mirrors the Python validator so that a contract validated by
// either component yields identical findings. It is intended for hot paths
// where envelopes stream through a gateway and low-latency checking matters.

return Cli.Run(args);

internal static class Cli
{
    public static int Run(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.WriteLine("usage: ProtocolArc.Runtime <validate|describe|selfcheck> ...");
            return 3;
        }

        try
        {
            return args[0] switch
            {
                "validate" => Validate(args),
                "describe" => Describe(args),
                "selfcheck" => SelfCheck(),
                _ => Unknown(args[0])
