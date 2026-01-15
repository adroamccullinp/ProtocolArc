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
            var payload = records
                .OrderBy(r => r.env.Source, StringComparer.Ordinal)
                .Select(r => new
                {
                    envelope = r.env.Source,
                    contract = contract.Name,
                    revision = contract.Revision,
                    ok = r.ok,
                    findings = r.findings.Select(f => new
                    {
                        rule = f.Rule, field = f.Field, severity = f.Severity, message = f.Message
                    })
                });
            Console.WriteLine(JsonSerializer.Serialize(payload,
                new JsonSerializerOptions { WriteIndented = true }));
        }
        else
        {
            foreach (var r in records.OrderBy(r => r.env.Source, StringComparer.Ordinal))
            {
                Console.WriteLine($"[{(r.ok ? "PASS" : "FAIL")}] {contract.Identity()} <- {r.env.Source}");
                foreach (var f in r.findings)
                    Console.WriteLine($"    {f.Severity.ToUpperInvariant(),-7} {f.Rule,-22} {f.Field}: {f.Message}");
            }
        }

        return allOk ? 0 : 1;
    }

    private static int Describe(string[] args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("usage: describe <contract.json>");
            return 3;
        }
        var contract = LoadContract(args[1]);
        Console.WriteLine($"{contract.Title} [{contract.Kind}] {contract.Identity()}");
        Console.WriteLine($"strict={contract.Strict} fields={contract.Fields.Count}");
        foreach (var spec in contract.Fields)
        {
            var req = spec.Required ? "required" : "optional";
            Console.WriteLine($"  {spec.Name,-28} {spec.TypeLabel(),-18} {req}");
        }
        return 0;
    }

    // A self-contained sanity check used by CI to confirm the runtime works
    // without any external fixtures. It builds a contract and two envelopes in
    // memory and asserts the expected pass/fail split.
    private static int SelfCheck()
    {
        const string contractJson = """
        {
          "name": "mcp.tool_call",
          "revision": "1.0.0",
          "kind": "mcp",
          "fields": [
            { "name": "method", "type": "string", "enum": ["tools/call"] },
            { "name": "params.name", "type": "string" },
            { "name": "params.arguments", "type": "object", "required": false }
          ]
        }
        """;
        const string goodJson = """
        { "contract": "mcp.tool_call",
          "data": { "method": "tools/call", "params": { "name": "search" } } }
        """;
        const string badJson = """
        { "contract": "mcp.tool_call",
          "data": { "method": "tools/list", "params": {} } }
        """;

        using var cdoc = JsonDocument.Parse(contractJson);
        var contract = Loader.ParseContract(cdoc.RootElement, "<selfcheck>");

        using var gdoc = JsonDocument.Parse(goodJson);
        var good = Loader.ParseEnvelope(gdoc.RootElement, "good");
        using var bdoc = JsonDocument.Parse(badJson);
        var bad = Loader.ParseEnvelope(bdoc.RootElement, "bad");

        var goodFindings = Validator.Validate(contract, good);
        var badFindings = Validator.Validate(contract, bad);

        bool goodOk = !Validator.HasError(goodFindings);
        bool badOk = !Validator.HasError(badFindings);

        Console.WriteLine($"selfcheck good={(goodOk ? "PASS" : "FAIL")} bad={(badOk ? "PASS" : "FAIL")}");
        if (goodOk && !badOk)
        {
            Console.WriteLine("selfcheck: OK");
            return 0;
        }
        Console.Error.WriteLine("selfcheck: FAILED");
        return 1;
    }
}

# draft note 22
