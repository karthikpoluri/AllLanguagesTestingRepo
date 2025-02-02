package my.app;

public class Example extends BaseClass implements Runnable {

    private int value;

    public Example(int value) {
        this.value = value;
    }

    public int add(int a, int b) {
        return a + b;
    }

    public void run() {
        System.out.println("Running...");
        add(3, 4);
    }
}
