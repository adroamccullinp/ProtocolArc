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
            };
        }
        catch (ContractException ex)
        {
            Console.Error.WriteLine($"error: {ex.Message}");
            return 3;
        }
        catch (FileNotFoundException ex)
        {
            Console.Error.WriteLine($"error: file not found: {ex.FileName}");
            return 3;
        }
    }

    private static int Unknown(string cmd)
    {
        Console.Error.WriteLine($"error: unknown command '{cmd}'");
        return 3;
    }

    private static Contract LoadContract(string path)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        return Loader.ParseContract(doc.RootElement, Path.GetFileName(path));
    }

    private static IEnumerable<Envelope> LoadEnvelopes(string path)
    {
        var name = Path.GetFileName(path);
        var envelopes = new List<Envelope>();
        if (path.EndsWith(".jsonl", StringComparison.OrdinalIgnoreCase))
        {
            int lineno = 0;
            foreach (var line in File.ReadLines(path))
            {
                lineno++;
                if (string.IsNullOrWhiteSpace(line)) continue;
                using var doc = JsonDocument.Parse(line);
                envelopes.Add(Loader.ParseEnvelope(doc.RootElement, $"{name}:{lineno}"));
            }
            return envelopes;
        }

        using var whole = JsonDocument.Parse(File.ReadAllText(path));
        if (whole.RootElement.ValueKind == JsonValueKind.Array)
        {
            int idx = 0;
            foreach (var item in whole.RootElement.EnumerateArray())
                envelopes.Add(Loader.ParseEnvelope(item, $"{name}[{idx++}]"));
        }
        else
        {
            envelopes.Add(Loader.ParseEnvelope(whole.RootElement, name));
        }
        return envelopes;
    }

    private static int Validate(string[] args)
    {
        if (args.Length < 3)
        {
            Console.Error.WriteLine("usage: validate <contract.json> <envelope> [--json]");
            return 3;
        }
        bool json = args.Contains("--json");
        var contract = LoadContract(args[1]);
        var envelopes = LoadEnvelopes(args[2]);

        bool allOk = true;
        var records = new List<(Envelope env, List<Finding> findings, bool ok)>();
        foreach (var env in envelopes)
        {
            var findings = Validator.Validate(contract, env);
            bool ok = !Validator.HasError(findings);
            allOk &= ok;
            records.Add((env, findings, ok));
        }

        if (json)
        {
