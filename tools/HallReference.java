// Optional external reference adapter. Original adapter code, not Choco source.
// Java 11+ source-file mode avoids Maven and keeps dependencies outside the project.
import java.util.*;
import org.chocosolver.solver.Model;
import org.chocosolver.solver.variables.IntVar;
import org.chocosolver.solver.exception.ContradictionException;
class HallReference {
 public static void main(String[] args) {
  Scanner in=new Scanner(System.in);String mode=args.length>0?args[0]:"AC_REGIN";
  while(in.hasNextInt()) {
   int n=in.nextInt(),m=in.nextInt();Model model=new Model("HallLab reference");IntVar[] vars=new IntVar[n];boolean empty=false;
   for(int i=0;i<n;i++) {int k=in.nextInt();int[] values=new int[k];for(int j=0;j<k;j++)values[j]=in.nextInt();if(k==0){empty=true;vars[i]=model.intVar("x"+i,0);}else vars[i]=model.intVar("x"+i,values);}
   // Choco constructors reject empty domains. Encode that exact false background,
   // rather than letting this adapter classify it without running propagation.
   if(empty)model.falseConstraint().post();
   if(n>0)model.allDifferent(vars,mode).post();else model.trueConstraint().post();
   try {model.getSolver().propagate();StringJoiner out=new StringJoiner(";");for(IntVar v:vars){StringJoiner row=new StringJoiner(",");for(int val=v.getLB();val<=v.getUB();val=v.nextValue(val))row.add(Integer.toString(val));out.add(row.toString());}System.out.println("S|"+out);}
   catch(ContradictionException e){System.out.println("U");}
  }
 }
}
