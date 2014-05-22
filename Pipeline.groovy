
class Pipeline
{
    def name;
    def input;
    def steps;
    def converters;
    
    Pipeline(name, data, converters=null)
    {
        this.name = name;
        this.input = data;
        this.steps = [];
        this.converters = converters;
    }

    def void add_step(service_container)
    {
        this.steps.add(service_container);
    }

    def void run()
    {
        println "\nRUNNING: " + this.name + "\n";
        def t0 = System.currentTimeMillis();
        String results_dir = 'data/out-' + this.name + '-' + t0;
        Data data = this.input;
        new File(results_dir).mkdir();
        for (step in this.steps) {
            data  = run_step(step, results_dir, data); }
        if (DiscriminatorRegistry.get(data.discriminator) == 'gate') {
            data = this.converters.gate2json.service.execute(data);
            print_result(this.converters.gate2json, results_dir, data, System.currentTimeMillis()); }
        def total_time = System.currentTimeMillis() - t0;
        println "\nTotal time elapsed: " + total_time + " ms\n";
    }

    def run_step(step, results_dir, data)
    {
        def t1 = System.currentTimeMillis();
        def format_in = DiscriminatorRegistry.get(data.discriminator);
        println step.name + '  ' + format_in;
        if (format_in == 'gate' && step.name.substring(4,8) != 'gate') {
            println '   converting: gate --> json';
            data = this.converters.gate2json.service.execute(data);
            print_result(this.converters.gate2json, results_dir, data, System.currentTimeMillis());
        }
        else if (format_in == 'json' && step.name.substring(4,8) == 'gate') {
            println '   converting: json --> gate';
            data = this.converters.json2gate.service.execute(data);
            print_result(this.converters.json2gate, results_dir, data, System.currentTimeMillis());
        }
        Data result = step.service.execute(data);
        def t2 = System.currentTimeMillis();
        print_result(step, results_dir, result, t2);
        return result;
    }

    def print_result(step, results_dir, result, t2)
    {
        def outfile = new File(results_dir + '/' + t2 + '-' + step.name + '.txt');
        def format = DiscriminatorRegistry.get(result.discriminator);
        if (format == 'json') {
            Container container = new Container(result.payload);
            outfile.setText(container.toPrettyJson(), 'UTF-8'); }
        else {
            outfile.setText(result.payload, 'UTF-8'); }
    }
    
}
