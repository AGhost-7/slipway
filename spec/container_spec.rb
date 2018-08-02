# To test this, we create a container then go into it to check
# what worked or not.

require 'pathname'
require 'dev_dock/options'
require 'dev_dock/container'
require 'open3'
require 'fileutils'

RSpec.describe DevDock::DevContainer do

  def path_parts(path)
    Pathname.new(path).each_filename.to_a
  end

  def remap_home(path)
    outer = path_parts(ENV['DEV_DOCK_HOST_HOME'])
    inner = path_parts(path)
    expect(outer[0]).to eql(inner[0])
    remapped = [outer[0], outer[1]].concat(inner.slice(2, inner.length))

    "/" + File.join(remapped)
  end

  def container_run(options, *run_command)
    options.instance_variable_set(:@image_name, 'aghost7/power-tmux')
    options.instance_variable_set(:@run_command, run_command)
    options.parse_env
    container = DevDock::DevContainer.new(options)
    script = container.run_arguments.join(' ')
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
    test_directory = ENV['DEV_DOCK_TEST_DIR'] || File.join(Dir.pwd, '.test-dir')
    mount_directory = test_directory
    if ENV['DEV_DOCK_HOST_HOME']
      mount_directory = remap_home(mount_directory)
    end
    if not Dir.exist?(test_directory)
      FileUtils.mkdir_p(test_directory)
    end
    File.write(File.join(test_directory, 'foo'), 'bar')
    options = DevDock::Options.new []
    options.instance_variable_set(:@volumes, ["#{mount_directory}:/baz"])
    stdin, stdout = container_run(options, "cat /baz/foo")
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
