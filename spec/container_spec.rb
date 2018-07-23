# To test this, we create a container then go into it to check
# what worked or not.

require 'dev_dock/options'
require 'dev_dock/container'
require 'open3'
require 'fileutils'

RSpec.describe DevDock::DevContainer do

  def container_run(options, *run_command)
    options.instance_variable_set(:@image_name, 'aghost7/power-tmux')
    options.instance_variable_set(:@run_command, run_command)
    container = DevDock::DevContainer.new(options)
    script = container.run_arguments.join(' ')
    puts "Full command: #{script}"
    environment = { 'command' => script }
    Open3.popen3(environment, 'script -q -c "$command"')
  end

  before(:all) do
    options = DevDock::Options.new []
    options.instance_variable_set(:@image_name, 'aghost7/power-tmux')
    container = DevDock::DevContainer.new(options)
    container.image.pull
    container.volumes.create
  end

  it 'forwards custom environment variables' do
    options = DevDock::Options.new []
    options.instance_variable_set(:@environment, ['SAMPLE_ENVIRONMENT=1'])
    stdin, stdout = container_run(options, 'env')
    env = stdout.read
    expect(env.include?('SAMPLE_ENVIRONMENT')).to eql(true)
  end

  it 'allows custom volumes' do
    skip
    test_directory = ENV['DEV_DOCK_TEST_DIR'] || File.join(Dir.pwd, '.test-dir')
    test_volume = File.join(test_directory, 'volume')
    if not Dir.exist?(test_volume)
      FileUtils.mkdir_p(test_volume)
    end
    File.write(File.join(test_volume, 'foo'), 'bar')
    options = DevDock::Options.new []
    options.instance_variable_set(:@volumes, ["#{test_volume}:/baz"])
    stdin, stdout = container_run(options, "ls /baz")
    expect(stdout.read).to eql('bar')
  end

  it 'allows the host ssh to work from the container' do
    skip
  end

  it 'allows the host to be reachable from localhost' do
    # Maybe use SimpleHTTPServer? probably something better for this.
    skip
  end

  it 'enables x11 forwarding' do
    # check by using xclip
    skip
  end

  it 'allows me to work docker commands without sudo' do
    skip
  end


end
